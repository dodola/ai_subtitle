from pydantic import BaseModel
from typing import Optional, Dict, Any

class VideoInfo(BaseModel):
    duration: float
    width: int
    height: int

class ROIBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class ExtractRequest(BaseModel):
    filename: str
    start_time: float = 0
    end_time: Optional[float] = None
    frame_interval: float = 1.0
    roi: ROIBox

class ExtractResponse(BaseModel):
    success: bool
    srt_content: Optional[str] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

class UploadResponse(BaseModel):
    filename: str
    duration: float
    width: int
    height: int
