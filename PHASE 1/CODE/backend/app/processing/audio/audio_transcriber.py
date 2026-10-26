import os
import re
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Any
import imageio_ffmpeg

from app.core.config import settings
from app.models.schemas import TranscriptItem, WordTimestampItem

logger = logging.getLogger("chronolens.processing.audio")
# (keep functions above)



def normalize_transcript_text(text: str) -> str:
    """Normalizes transcript text for high-accuracy text search."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


class AudioTranscriber:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or getattr(settings, "WHISPER_MODEL", "large-v3-turbo")
        self.model = None
        self.engine_type: Optional[str] = None

    def _load_model(self):
        """Loads and caches Whisper model ONCE at startup/first call."""
        if self.model is not None:
            return

        model_name = self.model_name
        compute_type = getattr(settings, "WHISPER_COMPUTE_TYPE", "float16")
        
        # 1. Try faster_whisper with CUDA (float16 / int8_float16)
        try:
            # Register torch lib DLL directory on Windows for CTranslate2 cublas64_12.dll
            try:
                import sys
                torch_lib = Path(sys.prefix) / "Lib" / "site-packages" / "torch" / "lib"
                if torch_lib.exists():
                    if hasattr(os, "add_dll_directory"):
                        os.add_dll_directory(str(torch_lib))
                    os.environ["PATH"] = str(torch_lib) + os.pathsep + os.environ.get("PATH", "")
            except Exception:
                pass

            from faster_whisper import WhisperModel
            logger.info(f"[AudioTranscriber] Loading faster-whisper model '{model_name}' on CUDA (compute_type={compute_type})...")
            try:
                self.model = WhisperModel(model_name, device="cuda", compute_type=compute_type)
            except Exception as cuda_err:
                logger.warning(f"[AudioTranscriber] CUDA float16 load failed ({cuda_err}), falling back to int8_float16 on CUDA...")
                self.model = WhisperModel(model_name, device="cuda", compute_type="int8_float16")
            
            self.engine_type = "faster_whisper"
            logger.info(f"[AudioTranscriber] faster-whisper model '{model_name}' loaded successfully.")
            return
        except Exception as fw_err:
            logger.warning(f"[AudioTranscriber] faster-whisper load failed or unavailable: {fw_err}")

        # 2. Fallback to standard OpenAI Whisper
        try:
            import whisper
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"[AudioTranscriber] Fallback: Loading OpenAI Whisper model '{model_name}' on device '{device}'...")
            self.model = whisper.load_model(model_name, device=device)
            self.engine_type = "openai_whisper"
            logger.info(f"[AudioTranscriber] OpenAI Whisper model '{model_name}' loaded successfully.")
            return
        except Exception as oai_err:
            logger.error(f"[AudioTranscriber] OpenAI Whisper fallback also failed: {oai_err}")
            raise RuntimeError(f"Whisper Model Load Failure: {oai_err}")

    def transcribe_video_audio(self, video_path: Path, video_id: str) -> List[TranscriptItem]:
        """
        Extracts audio from video file and runs Whisper transcription during video indexing.
        Returns a list of TranscriptItem objects.
        """
        logger.info(f"[AudioTranscriber] Extracting audio and transcribing for video_id={video_id}")
        
        audio_output_path = video_path.parent / f"{video_id}_audio.wav"
        
        # 1. Extract audio with FFmpeg (16kHz mono PCM)
        ffmpeg_exe = None
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_exe = "ffmpeg"

        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(audio_output_path)
        ]

        has_audio = False
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if audio_output_path.exists() and audio_output_path.stat().st_size > 1000:
                has_audio = True
                logger.info(f"[AudioTranscriber] Audio extracted successfully to {audio_output_path}")
            else:
                logger.info(f"[AudioTranscriber] Video has no active audio track or silent audio.")
        except Exception as e:
            logger.warning(f"[AudioTranscriber] Audio extraction failed: {str(e)}")

        if not has_audio:
            if audio_output_path.exists():
                audio_output_path.unlink()
            return []

        # 2. Run Whisper Transcription
        transcripts: List[TranscriptItem] = []
        try:
            self._load_model()

            if self.engine_type == "faster_whisper":
                use_vad = getattr(settings, "WHISPER_VAD_FILTER", True)
                lang = getattr(settings, "WHISPER_LANGUAGE", "en")
                beam_sz = getattr(settings, "WHISPER_BEAM_SIZE", 5)
                temp = getattr(settings, "WHISPER_TEMPERATURE", 0.0)
                cond_prev = getattr(settings, "WHISPER_CONDITION_ON_PREVIOUS_TEXT", True)

                no_speech_thresh = getattr(settings, "WHISPER_NO_SPEECH_THRESHOLD", 0.60)
                comp_ratio_thresh = getattr(settings, "WHISPER_COMPRESSION_RATIO_THRESHOLD", 2.4)
                log_prob_thresh = getattr(settings, "WHISPER_LOG_PROB_THRESHOLD", -1.0)
                compute_tp = getattr(settings, "WHISPER_COMPUTE_TYPE", "float16")

                vad_params = dict(min_silence_duration_ms=500, threshold=0.5, speech_pad_ms=250) if use_vad else None

                transcribe_kwargs = {
                    "beam_size": beam_sz,
                    "temperature": temp,
                    "condition_on_previous_text": cond_prev,
                    "word_timestamps": True,
                    "vad_filter": use_vad,
                }
                if vad_params:
                    transcribe_kwargs["vad_parameters"] = vad_params
                if lang and lang.lower() != "auto":
                    transcribe_kwargs["language"] = lang.lower()

                logger.info(
                    f"[AudioTranscriber] Starting transcription with model='{self.model_name}', "
                    f"beam_size={beam_sz}, temp={temp}, cond_prev={cond_prev}, language='{lang}'"
                )

                segments, info = self.model.transcribe(
                    str(audio_output_path),
                    **transcribe_kwargs
                )
                detected_language = info.language or (lang if lang and lang != "auto" else "en")

                seg_idx = 0
                for seg in segments:
                    raw_text = seg.text.strip()
                    if not raw_text:
                        continue

                    no_speech_p = float(getattr(seg, "no_speech_prob", 0.0))
                    comp_ratio = float(getattr(seg, "compression_ratio", 1.0))
                    avg_logprob = float(getattr(seg, "avg_logprob", 0.0))

                    # 1. Silence / Noise hallucination filter: reject high no-speech prob with low log probability
                    if no_speech_p > no_speech_thresh and avg_logprob < log_prob_thresh:
                        logger.debug(
                            f"[AudioTranscriber] Filtered hallucination/no-speech segment: '{raw_text}' "
                            f"(no_speech_prob={no_speech_p:.2f}, log_prob={avg_logprob:.2f})"
                        )
                        continue

                    # 2. Repeated text hallucination filter
                    if comp_ratio > comp_ratio_thresh:
                        logger.debug(
                            f"[AudioTranscriber] Filtered repeated text hallucination segment: '{raw_text}' "
                            f"(compression_ratio={comp_ratio:.2f})"
                        )
                        continue

                    seg_idx += 1
                    start_t = round(float(seg.start), 2)
                    end_t = round(float(seg.end), 2)
                    confidence = round(avg_logprob, 4)

                    words_list: List[WordTimestampItem] = []
                    if hasattr(seg, "words") and seg.words:
                        for w in seg.words:
                            w_str = getattr(w, "word", "").strip()
                            if w_str:
                                words_list.append(
                                    WordTimestampItem(
                                        word=w_str,
                                        startTime=round(float(getattr(w, "start", start_t)), 2),
                                        endTime=round(float(getattr(w, "end", end_t)), 2),
                                    )
                                )

                    transcripts.append(
                        TranscriptItem(
                            videoId=video_id,
                            segmentId=f"{video_id}_seg_{seg_idx:04d}",
                            startTime=start_t,
                            endTime=end_t,
                            text=raw_text,
                            normalizedText=normalize_transcript_text(raw_text),
                            language=detected_language,
                            confidence=confidence,
                            words=words_list if words_list else None,
                            whisperModel=self.model_name,
                            runtime=self.engine_type,
                            computeType=compute_tp,
                            vadEnabled=use_vad,
                            wordTimestampsEnabled=True,
                        )
                    )

            else:
                # Standard OpenAI Whisper
                lang = getattr(settings, "WHISPER_LANGUAGE", "en")
                compute_tp = getattr(settings, "WHISPER_COMPUTE_TYPE", "float16")
                use_vad = getattr(settings, "WHISPER_VAD_FILTER", True)

                opts = {"fp16": False, "word_timestamps": True}
                if lang and lang.lower() != "auto":
                    opts["language"] = lang.lower()

                result = self.model.transcribe(str(audio_output_path), **opts)
                detected_language = result.get("language", lang or "en")
                segments = result.get("segments", [])

                for idx, seg in enumerate(segments, start=1):
                    raw_text = seg.get("text", "").strip()
                    if not raw_text:
                        continue
                    start_t = round(float(seg.get("start", 0.0)), 2)
                    end_t = round(float(seg.get("end", 0.0)), 2)

                    words_list: List[WordTimestampItem] = []
                    if "words" in seg and seg["words"]:
                        for w in seg["words"]:
                            w_str = w.get("word", "").strip()
                            if w_str:
                                words_list.append(
                                    WordTimestampItem(
                                        word=w_str,
                                        startTime=round(float(w.get("start", start_t)), 2),
                                        endTime=round(float(w.get("end", end_t)), 2),
                                    )
                                )

                    transcripts.append(
                        TranscriptItem(
                            videoId=video_id,
                            segmentId=f"{video_id}_seg_{idx:04d}",
                            startTime=start_t,
                            endTime=end_t,
                            text=raw_text,
                            normalizedText=normalize_transcript_text(raw_text),
                            language=detected_language,
                            confidence=1.0,
                            words=words_list if words_list else None,
                            whisperModel=self.model_name,
                            runtime=self.engine_type,
                            computeType=compute_tp,
                            vadEnabled=use_vad,
                            wordTimestampsEnabled=True,
                        )
                    )

            logger.info(f"[AudioTranscriber] Transcription generated {len(transcripts)} timestamped segments.")

        except Exception as e:
            logger.error(f"[AudioTranscriber] Whisper transcription error: {str(e)}")
        finally:
            # Clean up temp audio file
            if audio_output_path.exists():
                try:
                    audio_output_path.unlink()
                except Exception:
                    pass

        return transcripts

    def reindex_video_transcripts(self, video_id: str, video_path: Optional[Path] = None) -> List[TranscriptItem]:
        """
        Re-indexes audio transcription for a specific video using the current high-accuracy Whisper configuration.
        Updates both MongoDB and storage/metadata/transcripts.json without re-uploading or re-processing frames.
        """
        import json
        from app.database.mongo import mongo_db

        logger.info(f"[AudioTranscriber] Re-indexing audio transcripts for video_id={video_id}")
        v_path = video_path

        if v_path is None or not v_path.exists():
            # Search candidate video locations
            search_dirs = [
                settings.VIDEOS_DIR,
                settings.STORAGE_DIR / "videos",
                settings.BASE_DIR / "app" / "uploads",
                settings.BASE_DIR / "storage" / "videos"
            ]
            for sd in search_dirs:
                if sd.exists():
                    for ext in ["mp4", "avi", "mov", "mkv", "webm"]:
                        cand = sd / f"{video_id}.{ext}"
                        if cand.exists():
                            v_path = cand
                            break
                        # Check matching prefix
                        matches = list(sd.glob(f"*{video_id}*.{ext}"))
                        if matches:
                            v_path = matches[0]
                            break

        if v_path is None or not v_path.exists():
            raise FileNotFoundError(f"[AudioTranscriber] Video file not found for video_id={video_id}")

        transcripts = self.transcribe_video_audio(video_path=v_path, video_id=video_id)
        transcripts_dicts = [tr.dict() for tr in transcripts]

        # 1. Update MongoDB
        try:
            mongo_db.connect()
            mongo_db.insert_transcripts(transcripts_dicts, video_id=video_id)
        except Exception as m_err:
            logger.warning(f"[AudioTranscriber] MongoDB transcript update notice: {m_err}")

        # 2. Update metadata JSON on disk
        try:
            meta_dir = settings.BASE_DIR / "storage" / "metadata"
            meta_dir.mkdir(parents=True, exist_ok=True)
            t_file = meta_dir / "transcripts.json"
            existing_segs = []
            if t_file.exists():
                try:
                    with open(t_file, "r", encoding="utf-8") as _tf:
                        existing_segs = json.load(_tf)
                except Exception:
                    existing_segs = []

            existing_segs = [s for s in existing_segs if isinstance(s, dict) and s.get("videoId") != video_id]
            clean_dicts = []
            for td in transcripts_dicts:
                c_td = dict(td)
                c_td.pop("_id", None)
                clean_dicts.append(c_td)
            existing_segs.extend(clean_dicts)
            with open(t_file, "w", encoding="utf-8") as _tf:
                json.dump(existing_segs, _tf, indent=2)
            logger.info(f"[AudioTranscriber] Persisted {len(transcripts)} transcripts to {t_file}")
        except Exception as _fe:
            logger.warning(f"[AudioTranscriber] Transcripts JSON update failed: {_fe}")

        return transcripts


transcriber = AudioTranscriber()

