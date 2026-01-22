import cv2
import logging
import numpy as np
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class VideoProcessor:
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        logger.info(f"Getting video info: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video file: {video_path}")
            raise Exception("Cannot open video file")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        info = {
            "duration": duration,
            "fps": fps,
            "width": width,
            "height": height,
            "frame_count": frame_count
        }
        logger.info(f"Video info: duration={duration:.2f}s, {width}x{height}, fps={fps}")
        
        return info
    
    def extract_frames(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        frame_interval: float,
        roi: Dict[str, int]
    ) -> List[Tuple[float, np.ndarray]]:
        logger.info(f"Extracting frames from {video_path}")
        logger.info(f"  Time range: {start_time}s to {end_time}s")
        logger.info(f"  Frame interval: {frame_interval}s")
        logger.info(f"  ROI: {roi}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video file: {video_path}")
            raise Exception("Cannot open video file")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        logger.info(f"Video FPS: {fps}")
        
        frames = []
        
        roi_x = max(0, roi.get('x', 0))
        roi_y = max(0, roi.get('y', 0))
        roi_w = max(1, roi.get('width', 1))
        roi_h = max(1, roi.get('height', 1))
        logger.info(f"ROI parameters: x={roi_x}, y={roi_y}, w={roi_w}, h={roi_h}")
        
        timestamps = self._generate_timestamps(start_time, end_time, frame_interval)
        logger.info(f"Generated {len(timestamps)} timestamps")
        
        for timestamp in timestamps:
            frame_idx = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                x1 = min(roi_x, w - 1)
                y1 = min(roi_y, h - 1)
                x2 = min(x1 + roi_w, w)
                y2 = min(y1 + roi_h, h)
                
                if x2 > x1 and y2 > y1:
                    cropped = frame[y1:y2, x1:x2]
                    frames.append((timestamp, cropped))
                    logger.debug(f"Extracted frame at {timestamp}s, shape: {cropped.shape}")
        
        cap.release()
        logger.info(f"Finished extracting {len(frames)} frames")
        
        return frames
    
    def _generate_timestamps(
        self,
        start_time: float,
        end_time: float,
        interval: float
    ) -> List[float]:
        timestamps = []
        current = start_time
        while current <= end_time:
            timestamps.append(round(current, 2))
            current += interval
        return timestamps
