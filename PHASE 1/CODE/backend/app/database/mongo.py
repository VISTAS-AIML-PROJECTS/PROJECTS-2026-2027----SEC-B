import logging
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from app.core.config import settings

logger = logging.getLogger("chronolens.database")


class MongoDBConnectionError(Exception):
    """Raised when MongoDB connection or operation fails."""
    pass


class MongoDBClient:
    def __init__(self, uri: str = None, db_name: str = None):
        self.uri = uri or settings.MONGODB_URI
        self.db_name = db_name or settings.MONGODB_DB_NAME
        self._client: Optional[MongoClient] = None
        self._db = None
        self._is_offline = False
        self._last_offline_time = 0.0

    def connect(self):
        """Initializes PyMongo client connection with fallback mechanisms and fast offline failure state."""
        import time

        # Fast offline check: if DB failed recently (<30s ago), use in-memory mongomock without socket timeout penalty
        now = time.time()
        if self._is_offline and (now - self._last_offline_time) < 30.0:
            if self._db is None:
                try:
                    import mongomock
                    self._client = mongomock.MongoClient()
                    self._db = self._client[self.db_name]
                    self._restore_backup()
                except Exception:
                    pass
            return

        # 1. Try Primary URI (Atlas / Configured) with SSL invalid cert allowance
        try:
            self._client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=300,
                connectTimeoutMS=300,
                socketTimeoutMS=500,
                tlsAllowInvalidCertificates=True
            )
            self._client.admin.command("ping")
            self._db = self._client[self.db_name]
            self._is_offline = False
            logger.info(f"Connected to Primary MongoDB database '{self.db_name}' at {self.uri}")
            try:
                if self._db.videos.count_documents({}) == 0:
                    self._restore_backup()
            except Exception as b_err:
                logger.warning(f"Backup restore notice: {str(b_err)}")
            return
        except Exception as e:
            logger.debug(f"Primary MongoDB connection failed at {self.uri} ({str(e)}). Attempting Local Fallback...")

        # 2. Try Local Fallback (mongodb://localhost:27017)
        try:
            local_uri = "mongodb://localhost:27017"
            self._client = MongoClient(
                local_uri,
                serverSelectionTimeoutMS=300,
                connectTimeoutMS=300,
                socketTimeoutMS=500
            )
            self._client.admin.command("ping")
            self._db = self._client[self.db_name]
            self._is_offline = False
            logger.info(f"Connected to Local Fallback MongoDB database '{self.db_name}' at {local_uri}")
            try:
                if self._db.videos.count_documents({}) == 0:
                    self._restore_backup()
            except Exception as b_err:
                logger.warning(f"Backup restore notice: {str(b_err)}")
            return
        except Exception as e:
            logger.debug(f"Local MongoDB connection failed ({str(e)}). Using Mock In-Memory MongoDB Fallback.")

        # 3. Mark offline state and use mongomock / Mock Database Fallback
        self._is_offline = True
        self._last_offline_time = now
        try:
            import mongomock
            self._client = mongomock.MongoClient()
            self._db = self._client[self.db_name]
            logger.info("Using In-Memory mongomock client fallback (fast offline mode).")
            try:
                self._restore_backup()
            except Exception as b_err:
                logger.warning(f"Backup restore notice: {str(b_err)}")
            return
        except Exception as e:
            logger.error(f"Failed to initialize mongomock client fallback: {str(e)}")
            self._client = None
            self._db = None
            raise MongoDBConnectionError(f"MongoDB connection failed across all endpoints: {str(e)}")

    @property
    def db(self):
        if self._db is None:
            self.connect()
        return self._db

    def _save_backup(self):
        """Serializes MongoDB collections to disk JSON files for restart persistence."""
        try:
            backup_dir = settings.STORAGE_DIR / "metadata"
            backup_dir.mkdir(parents=True, exist_ok=True)
            cols = ["videos", "frames", "detections", "tracks", "transcripts", "embeddings", "attributes", "scenes", "ocr"]
            for col in cols:
                docs = list(self.db[col].find({}, {"_id": 0}))
                out_path = backup_dir / f"{col}.json"
                if not docs and out_path.exists() and out_path.stat().st_size > 5:
                    continue
                with open(out_path, "w", encoding="utf-8") as f:
                    import json
                    json.dump(docs, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Metadata backup save error: {str(e)}")

    def _restore_backup(self):
        """Loads metadata documents from disk JSON files into mock MongoDB collection."""
        try:
            backup_dir = settings.STORAGE_DIR / "metadata"
            if not backup_dir.exists():
                backup_dir = settings.BASE_DIR / "storage" / "metadata"
            if not backup_dir.exists():
                backup_dir = settings.BASE_DIR / "backend" / "storage" / "metadata"
            if not backup_dir.exists():
                return
            cols = ["videos", "frames", "detections", "tracks", "transcripts", "embeddings", "attributes", "scenes", "ocr"]
            restored_count = 0
            for col in cols:
                in_path = backup_dir / f"{col}.json"
                if in_path.exists() and in_path.stat().st_size > 5:
                    with open(in_path, "r", encoding="utf-8") as f:
                        import json
                        docs = json.load(f)
                    if docs:
                        self.db[col].delete_many({})
                        self.db[col].insert_many(docs)
                        restored_count += len(docs)
            if restored_count > 0:
                logger.info(f"[MongoDBClient] Restored {restored_count} metadata documents from disk backup ({backup_dir}).")
        except Exception as e:
            logger.warning(f"Metadata backup restore error: {str(e)}")

    def upsert_video(self, video_data: Dict[str, Any]) -> None:
        """Inserts or updates a video document in the 'videos' collection."""
        try:
            video_id = video_data.get("videoId")
            self.db.videos.update_one(
                {"videoId": video_id},
                {"$set": video_data},
                upsert=True
            )
            self._save_backup()
        except Exception as e:
            logger.error(f"MongoDB upsert_video error for {video_data.get('videoId')}: {str(e)}")
            raise MongoDBConnectionError(f"MongoDB write failed: {str(e)}")

    def update_video_status(
        self,
        video_id: str,
        status: str,
        current_stage: str,
        message: str,
        error: Optional[str] = None
    ) -> None:
        """Updates video processing stage and status."""
        try:
            update_fields = {
                "status": status,
                "currentStage": current_stage,
                "message": message,
                "updatedAt": settings.PROJECT_NAME,
            }
            if error:
                update_fields["error"] = error

            self.db.videos.update_one(
                {"videoId": video_id},
                {"$set": update_fields},
                upsert=True
            )
            self._save_backup()
        except Exception as e:
            logger.error(f"MongoDB update_video_status error for {video_id}: {str(e)}")
            raise MongoDBConnectionError(f"MongoDB update status failed: {str(e)}")

    def insert_frames(self, frames_data: List[Dict[str, Any]], video_id: Optional[str] = None) -> None:
        """Clears old frames for video_id and inserts frame metadata list into 'frames' collection."""
        vid = video_id or (frames_data[0].get("videoId") if frames_data else None)
        try:
            if vid:
                self.db.frames.delete_many({"videoId": vid})
            if frames_data:
                self.db.frames.insert_many(frames_data)
            self._save_backup()
        except Exception as e:
            logger.error(f"MongoDB insert_frames error: {str(e)}")
            raise MongoDBConnectionError(f"MongoDB insert frames failed: {str(e)}")

    def insert_detections(self, detections_data: List[Dict[str, Any]], video_id: Optional[str] = None) -> None:
        """Clears old detections for video_id and inserts detections into 'detections' collection."""
        vid = video_id or (detections_data[0].get("videoId") if detections_data else None)
        try:
            if vid:
                self.db.detections.delete_many({"videoId": vid})
            if detections_data:
                self.db.detections.insert_many(detections_data)
            self._save_backup()
        except Exception as e:
            logger.error(f"MongoDB insert_detections error: {str(e)}")
            raise MongoDBConnectionError(f"MongoDB insert detections failed: {str(e)}")

    def insert_tracks(self, tracks_data: List[Dict[str, Any]], video_id: Optional[str] = None) -> None:
        """Clears old tracks for video_id and inserts object tracks into 'tracks' collection."""
        vid = video_id or (tracks_data[0].get("videoId") if tracks_data else None)
        try:
            if vid:
                self.db.tracks.delete_many({"videoId": vid})
            if tracks_data:
                self.db.tracks.insert_many(tracks_data)
            self._save_backup()
        except Exception as e:
            logger.error(f"MongoDB insert_tracks error: {str(e)}")
            raise MongoDBConnectionError(f"MongoDB insert tracks failed: {str(e)}")

    def insert_transcripts(self, transcripts_data: List[Dict[str, Any]], video_id: Optional[str] = None) -> None:
        """Clears old transcripts for video_id and inserts transcript items into 'transcripts' collection."""
        vid = video_id or (transcripts_data[0].get("videoId") if transcripts_data else None)
        try:
            if vid:
                self.db.transcripts.delete_many({"videoId": vid})
            if transcripts_data:
                self.db.transcripts.insert_many(transcripts_data)
            self._save_backup()
        except Exception as e:
            logger.error(f"MongoDB insert_transcripts error: {str(e)}")
            raise MongoDBConnectionError(f"MongoDB insert transcripts failed: {str(e)}")

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves video record from 'videos' collection."""
        try:
            return self.db.videos.find_one({"videoId": video_id}, {"_id": 0})
        except Exception as e:
            logger.error(f"MongoDB get_video error: {str(e)}")
            raise MongoDBConnectionError(f"MongoDB read video failed: {str(e)}")

    def get_all_videos(self) -> List[Dict[str, Any]]:
        """Retrieves all video records from 'videos' collection."""
        try:
            return list(self.db.videos.find({}, {"_id": 0}))
        except Exception as e:
            logger.error(f"MongoDB get_all_videos error: {str(e)}")
            return []


    def get_summary(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Aggregates summary information for a processed video."""
        try:
            video_doc = self.db.videos.find_one({"videoId": video_id}, {"_id": 0})
            if not video_doc:
                return None

            frame_count = self.db.frames.count_documents({"videoId": video_id})
            detection_count = self.db.detections.count_documents({"videoId": video_id})
            track_count = self.db.tracks.count_documents({"videoId": video_id})
            transcripts = list(self.db.transcripts.find({"videoId": video_id}, {"_id": 0}))

            return {
                "videoId": video_id,
                "videoMetadata": video_doc,
                "frameCount": frame_count,
                "objectsDetected": detection_count,
                "trackCount": track_count,
                "transcriptLength": len(transcripts),
                "processingTime": video_doc.get("processingTime", "N/A"),
                "transcript": transcripts,
                "status": video_doc.get("status", "COMPLETED"),
                "error": video_doc.get("error")
            }
        except Exception as e:
            logger.error(f"MongoDB get_summary error for {video_id}: {str(e)}")
            raise MongoDBConnectionError(f"MongoDB query summary failed: {str(e)}")

    def insert_attributes(self, attributes_data: List[Dict[str, Any]], video_id: Optional[str] = None) -> None:
        """Clears old attributes for video_id and inserts attribute records into 'attributes' collection."""
        vid = video_id or (attributes_data[0].get("videoId") if attributes_data else None)
        try:
            if vid:
                self.db.attributes.delete_many({"videoId": vid})
            if attributes_data:
                self.db.attributes.insert_many(attributes_data)
            self._save_backup()
        except Exception as e:
            logger.error(f"MongoDB insert_attributes error: {str(e)}")

    def insert_scenes(self, scenes_data: List[Dict[str, Any]], video_id: Optional[str] = None) -> None:
        """Clears old scene records for video_id and inserts into 'scenes' collection."""
        vid = video_id or (scenes_data[0].get("videoId") if scenes_data else None)
        try:
            if vid:
                self.db.scenes.delete_many({"videoId": vid})
            if scenes_data:
                self.db.scenes.insert_many(scenes_data)
            self._save_backup()
        except Exception as e:
            logger.error(f"MongoDB insert_scenes error: {str(e)}")

    def insert_ocr_texts(self, ocr_data: List[Dict[str, Any]], video_id: Optional[str] = None) -> None:
        """Clears old OCR records for video_id and inserts OCR records into 'ocr' collection."""
        vid = video_id or (ocr_data[0].get("videoId") if ocr_data else None)
        try:
            if vid:
                self.db.ocr.delete_many({"videoId": vid})
            if ocr_data:
                self.db.ocr.insert_many(ocr_data)
            self._save_backup()
        except Exception as e:
            logger.error(f"MongoDB insert_ocr_texts error: {str(e)}")

    def get_ocr_texts(self, video_id: str) -> List[Dict[str, Any]]:
        """Retrieves all OCR text records for a video."""
        try:
            return list(self.db.ocr.find({"videoId": video_id}, {"_id": 0}))
        except Exception as e:
            logger.error(f"MongoDB get_ocr_texts error: {str(e)}")
            return []

    def get_attributes(self, video_id: str) -> List[Dict[str, Any]]:
        """Retrieves all attribute records for a video."""
        try:
            return list(self.db.attributes.find({"videoId": video_id}, {"_id": 0}))
        except Exception as e:
            logger.error(f"MongoDB get_attributes error: {str(e)}")
            return []

    def get_track_attributes(self, video_id: str, track_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves visual attributes record for a specific video track."""
        try:
            return self.db.attributes.find_one({"videoId": video_id, "trackId": track_id}, {"_id": 0})
        except Exception as e:
            logger.error(f"MongoDB get_track_attributes error: {str(e)}")
            return None

    def get_frame_scene(self, video_id: str, frame_number: int) -> Optional[Dict[str, Any]]:
        """Retrieves scene context record for a specific video frame."""
        try:
            return self.db.scenes.find_one({"videoId": video_id, "frameNumber": frame_number}, {"_id": 0})
        except Exception as e:
            logger.error(f"MongoDB get_frame_scene error: {str(e)}")
            return None

    def clear_all_collections(self) -> List[str]:
        """Purges all documents from all collections in database."""
        cleared = []
        try:
            collections = ["videos", "frames", "detections", "tracks", "transcripts", "embeddings", "attributes", "scenes", "ocr"]
            for col_name in collections:
                self.db[col_name].delete_many({})
                cleared.append(col_name)
            
            # Clear backup JSON files on disk
            backup_dir = settings.STORAGE_DIR / "metadata"
            if backup_dir.exists():
                for f in backup_dir.glob("*.json"):
                    try:
                        f.unlink()
                    except Exception:
                        pass

            logger.info(f"Cleared all MongoDB collections: {cleared}")
            return cleared
        except Exception as e:
            logger.error(f"MongoDB clear_all_collections error: {str(e)}")
            return ["videos", "frames", "detections", "tracks", "transcripts", "embeddings", "attributes", "scenes", "ocr"]


mongo_db = MongoDBClient()



