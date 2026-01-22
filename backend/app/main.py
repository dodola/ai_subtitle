import os
import logging
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
import shutil
import uuid

from app.services.video_processor import VideoProcessor
from app.services.ocr_service import OCRService
from app.services.subtitle_generator import SubtitleGenerator

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

upload_dir = os.environ.get("UPLOAD_DIR", "/app/uploads")
os.makedirs(upload_dir, exist_ok=True)

video_processor = VideoProcessor()
ocr_service = OCRService()
subtitle_generator = SubtitleGenerator()

app = FastAPI(title="AI Subtitle Extractor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    filename: str
    start_time: float = 0
    end_time: Optional[float] = None
    frame_interval: float = 1.0
    roi: dict

class ExtractResponse(BaseModel):
    success: bool
    srt_content: Optional[str] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "AI Subtitle Extractor API", "version": "1.0.0"}

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    logger.info(f"Upload request received: filename={file.filename}, content_type={file.content_type}")
    
    if file.content_type and not file.content_type.startswith("video/"):
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(status_code=400, detail="Only video files are allowed")
    
    file_ext = file.filename.split(".")[-1] if file.filename else "mp4"
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    logger.info(f"Saving file to: {file_path}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    logger.info(f"File saved, size: {os.path.getsize(file_path)} bytes")
    
    video_info = video_processor.get_video_info(file_path)
    logger.info(f"Video info: duration={video_info['duration']}, width={video_info['width']}, height={video_info['height']}")
    
    return {
        "filename": unique_filename,
        "duration": video_info["duration"],
        "width": video_info["width"],
        "height": video_info["height"]
    }

@app.post("/api/extract", response_model=ExtractResponse)
async def extract_subtitle(request: ExtractRequest):
    logger.info("=" * 50)
    logger.info("Extract request received")
    logger.info(f"  filename: {request.filename}")
    logger.info(f"  start_time: {request.start_time}")
    logger.info(f"  end_time: {request.end_time}")
    logger.info(f"  frame_interval: {request.frame_interval}")
    logger.info(f"  roi: {request.roi}")
    logger.info("=" * 50)
    
    start_time = time.time()
    
    file_path = os.path.join(upload_dir, request.filename)
    logger.info(f"Looking for file: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return ExtractResponse(
            success=False,
            error="Video file not found"
        )
    
    logger.info(f"File found, size: {os.path.getsize(file_path)} bytes")
    
    try:
        video_info = video_processor.get_video_info(file_path)
        logger.info(f"Video duration: {video_info['duration']} seconds")
        
        end_time = request.end_time or video_info["duration"]
        logger.info(f"Processing from {request.start_time}s to {end_time}s")
        
        logger.info("Extracting frames...")
        frames = video_processor.extract_frames(
            video_path=file_path,
            start_time=request.start_time,
            end_time=end_time,
            frame_interval=request.frame_interval,
            roi=request.roi
        )
        logger.info(f"Extracted {len(frames)} frames")
        
        ocr_results = []
        for i, (timestamp, frame) in enumerate(frames):
            logger.info(f"OCR processing frame {i+1}/{len(frames)} at {timestamp}s")
            try:
                text = ocr_service.recognize_text(frame)
                logger.info(f"  Frame {i+1} OCR result: '{text}'")
                if text and text.strip():
                    ocr_results.append({
                        "timestamp": timestamp,
                        "text": text.strip()
                    })
            except Exception as e:
                logger.error(f"  Frame {i+1} OCR error: {e}")
        
        logger.info(f"Total OCR results: {len(ocr_results)}")
        
        logger.info("Generating SRT...")
        srt_content = subtitle_generator.generate_srt(
            ocr_results,
            frame_interval=request.frame_interval
        )
        logger.info(f"SRT content length: {len(srt_content)} chars")
        
        processing_time = time.time() - start_time
        logger.info(f"Processing completed in {processing_time:.2f}s")
        
        return ExtractResponse(
            success=True,
            srt_content=srt_content,
            processing_time=round(processing_time, 2)
        )
    
    except Exception as e:
        logger.exception("Extract failed with error")
        return ExtractResponse(
            success=False,
            error=str(e)
        )

@app.get("/api/video/{filename}")
async def serve_video(filename: str):
    logger.info(f"Video stream request: {filename}")
    file_path = os.path.join(upload_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Video not found")
