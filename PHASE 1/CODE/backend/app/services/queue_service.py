import asyncio
import logging
from pathlib import Path
from typing import Dict, Any
from app.processing.coordinator import PipelineCoordinator

logger = logging.getLogger("chronolens.services.queue")


class ProcessingQueue:
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task = None
        self._is_running: bool = False

    async def start_worker(self):
        """Starts the background worker consuming the processing queue."""
        if not self._is_running:
            self._is_running = True
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("[ProcessingQueue] Background worker task started.")

    async def stop_worker(self):
        """Gracefully stops the background worker task."""
        if self._is_running:
            self._is_running = False
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            logger.info("[ProcessingQueue] Background worker task stopped.")

    async def enqueue_video(self, video_id: str, video_path: Path, original_filename: str):
        """Enqueues a video upload job into the processing queue."""
        job = {
            "video_id": video_id,
            "video_path": video_path,
            "original_filename": original_filename,
        }
        await self._queue.put(job)
        logger.info(f"[ProcessingQueue] Video {video_id} added to processing queue. Queue depth: {self._queue.qsize()}")

    async def _worker_loop(self):
        """Sequential task consumer loop."""
        while self._is_running:
            try:
                job: Dict[str, Any] = await self._queue.get()
                video_id = job["video_id"]
                video_path = job["video_path"]
                original_filename = job["original_filename"]

                logger.info(f"[Worker] Consuming job for video_id={video_id}")
                
                # Execute pipeline synchronously in threadpool executor to avoid blocking asyncio event loop
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    PipelineCoordinator.process_video,
                    video_id,
                    video_path,
                    original_filename
                )

                self._queue.task_done()
                logger.info(f"[Worker] Finished processing job for video_id={video_id}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Worker] Unexpected error processing video job: {str(e)}", exc_info=True)


queue_service = ProcessingQueue()
