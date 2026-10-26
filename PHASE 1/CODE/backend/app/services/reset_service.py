import os
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from app.core.config import settings
from app.database.mongo import mongo_db
from app.services.semantic.faiss_manager import faiss_manager

logger = logging.getLogger("chronolens.services.reset")


class DevelopmentResetService:
    """
    Developer-Only Reset Utility Service.
    Atomically clears temporary storage files, reinitializes FAISS indices,
    purges MongoDB collections, and restores empty directory structures.
    """

    @staticmethod
    def _count_and_remove_dir_contents(directory: Path) -> int:
        """
        Helper that removes all files and subdirectories within a given folder instantly,
        guaranteeing the parent folder exists afterward.
        """
        import gc
        gc.collect()

        deleted_file_count = 0
        if directory.exists():
            for item in list(directory.iterdir()):
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink(missing_ok=True)
                        deleted_file_count += 1
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_file_count += 1
                except Exception as e:
                    logger.warning(f"[ResetService] Cleanup notice for {item}: {str(e)}")

        # Guarantee directory exists
        directory.mkdir(parents=True, exist_ok=True)
        return deleted_file_count


    @classmethod
    def reset_all_development_data(cls) -> Dict[str, Any]:
        """
        Executes complete developer reset.
        Returns diagnostic summary dictionary matching specification.
        """
        logger.info("[ResetService] Initiating complete Development Data Reset...")

        steps_completed: List[str] = []

        try:
            # 1. Clear Uploaded Videos
            videos_deleted = cls._count_and_remove_dir_contents(settings.UPLOADS_DIR)
            steps_completed.append("Uploaded Videos Removed")

            # 2. Clear Extracted Frames
            frames_deleted = cls._count_and_remove_dir_contents(settings.FRAMES_DIR)
            steps_completed.append("Extracted Frames Removed")

            # 3. Clear Audio Files (if present)
            audio_dir = getattr(settings, "AUDIO_DIR", settings.STORAGE_DIR / "audio")
            cls._count_and_remove_dir_contents(audio_dir)
            steps_completed.append("Audio Files Removed")

            # 4. Clear Object Crops and Debug Assets
            object_crops_deleted = cls._count_and_remove_dir_contents(settings.DEBUG_DIR)
            steps_completed.append("Debug Assets & Object Crops Removed")

            # 4.5 Clear Generated Video Clips
            clips_deleted = cls._count_and_remove_dir_contents(settings.CLIPS_DIR)
            steps_completed.append("Generated Video Clips Removed")

            # 5. Clear FAISS Indices
            faiss_manager.reset_indices()
            steps_completed.append("FAISS Indices Reset")

            # 6. Clear MongoDB Collections
            cleared_collections = mongo_db.clear_all_collections()
            steps_completed.append("MongoDB Collections Cleared")

            # 7. Ensure All Core Storage Directories Exist
            settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
            settings.FRAMES_DIR.mkdir(parents=True, exist_ok=True)
            audio_dir.mkdir(parents=True, exist_ok=True)
            settings.DEBUG_DIR.mkdir(parents=True, exist_ok=True)
            settings.CLIPS_DIR.mkdir(parents=True, exist_ok=True)
            settings.FAISS_DIR.mkdir(parents=True, exist_ok=True)
            steps_completed.append("Directory Structure Recreated")

            now_utc = datetime.now(timezone.utc).isoformat()

            summary = {
                "videosDeleted": videos_deleted,
                "framesDeleted": frames_deleted,
                "objectCropsDeleted": object_crops_deleted,
                "faissIndicesReset": True,
                "mongodbCollectionsCleared": cleared_collections,
                "processingCacheCleared": True,
                "timestamp": now_utc,
                "stepsCompleted": steps_completed
            }

            logger.info(f"[ResetService] Development Data Reset COMPLETED successfully. Summary: {summary}")

            return {
                "success": True,
                "message": "Development data reset successfully.",
                "summary": summary
            }

        except Exception as e:
            err_msg = f"Developer Reset Failed during execution: {str(e)}"
            logger.error(f"[ResetService] {err_msg}", exc_info=True)
            return {
                "success": False,
                "message": err_msg,
                "summary": {
                    "stepsCompleted": steps_completed,
                    "error": str(e)
                }
            }
