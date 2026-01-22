import base64
import logging
import os
from ollama import Client
import numpy as np
import cv2
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip('/')

ollama_client = Client(host=OLLAMA_HOST)

class OCRService:
    def __init__(self, model_name: str = "qwen2.5vl:3b"):
        self.model_name = model_name
        logger.info(f"OCRService initialized with model: {model_name}, host: {OLLAMA_HOST}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        logger.debug(f"Preprocessing image, shape: {image.shape}")
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            logger.debug(f"Converted to grayscale: {gray.shape}")
        else:
            gray = image
        
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            11, 2
        )
        logger.debug(f"Applied adaptive threshold, shape: {binary.shape}")
        
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        logger.debug(f"Morphology cleanup complete, shape: {cleaned.shape}")
        
        return cleaned
    
    def recognize_text(self, image: np.ndarray) -> Optional[str]:
        logger.info("Starting OCR recognition")
        
        temp_file_path = None
        try:
            processed = self.preprocess_image(image)
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_file_path = temp_file.name
                cv2.imwrite(temp_file_path, processed)
            
            logger.info(f"Saved temp image to: {temp_file_path}")
            logger.debug(f"Temp file size: {os.path.getsize(temp_file_path)} bytes")
            
            logger.info(f"Calling Ollama API with model: {self.model_name} at {OLLAMA_HOST}")
            response = ollama_client.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': '请准确提取图片中的字幕文本，只返回字幕内容，不要添加任何解释或格式。如果图像中没有字幕，返回"EMPTY"。',
                    'images': [temp_file_path]
                }],
                options={
                    "temperature": 0.1,
                    "num_predict": 100
                }
            )
            
            text = response.get('message', {}).get('content', '').strip()
            logger.info(f"OCR raw response: '{text}'")
            
            if text == 'EMPTY':
                logger.info("No subtitle found in image")
                return None
            
            result = text if text else None
            logger.info(f"OCR result: '{result}'")
            return result
        
        except Exception as e:
            logger.exception(f"OCR Error: {e}")
            return None
        
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.debug(f"Removed temp file: {temp_file_path}")
