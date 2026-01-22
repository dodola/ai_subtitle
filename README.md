# AI Subtitle Extractor

A tool to extract hardcoded subtitles from videos using AI (Ollama + Qwen-VL).

## Features

- Upload video files
- Select subtitle region by drawing a box
- Configure extraction parameters (time range, frame interval)
- Extract subtitles using Qwen-VL OCR
- Export as SRT format

## Requirements

- Docker & Docker Compose
- Ollama (running on host machine)

## Ollama Setup (Host Machine)

Ollama 需要在宿主机上单独安装和运行。

### 1. Install Ollama

```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl start ollama

# Or run in background
ollama serve
```

### 2. Pull Vision Model

```bash
# Recommended: Qwen2-VL (smaller, CPU-friendly)
ollama pull qwen2-vl

# Alternative: LLaVA (larger, better quality)
ollama pull llava:7b
```

### 3. Verify Ollama

```bash
curl http://localhost:11434/api/version
# Should return version info
```

## Quick Start

```bash
# Start backend and frontend
docker compose up -d

# Access at http://localhost:3000
```

## Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
-**: http://localhost **Ollama:11434 (must be running on host)

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| OLLAMA_BASE_URL | http://host.docker.internal:11434 | Ollama API endpoint |
| UPLOAD_DIR | /app/uploads | Video upload directory |
| MAX_FILE_SIZE | 524288000 | Max file size (500MB) |

## API Endpoints

### POST /api/upload

Upload a video file.

**Response:**
```json
{
  "filename": "xxx.mp4",
  "duration": 120.5,
  "width": 1920,
  "height": 1080
}
```

### POST /api/extract

Extract subtitles from video.

**Request:**
```json
{
  "filename": "xxx.mp4",
  "start_time": 0,
  "end_time": 300,
  "frame_interval": 1.0,
  "roi": {
    "x": 100,
    "y": 500,
    "width": 400,
    "height": 50
  }
}
```

**Response:**
```json
{
  "success": true,
  "srt_content": "1\n00:00:00,000 --> 00:00:02,000\n字幕文本...",
  "processing_time": 12.5
}
```
