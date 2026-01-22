'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import axios from 'axios'
import { Upload, Play, Pause, Download, Copy, Trash2, Settings, Video } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface VideoInfo {
  duration: number
  width: number
  height: number
}

interface ExtractResult {
  success: boolean
  srt_content: string | null
  processing_time: number | null
  error: string | null
}

export default function Home() {
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null)
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null)
  const [isUploaded, setIsUploaded] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [roi, setRoi] = useState<{ x: number; y: number; width: number; height: number } | null>(null)
  const [startTime, setStartTime] = useState(0)
  const [endTime, setEndTime] = useState(0)
  const [frameInterval, setFrameInterval] = useState(1)
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState<ExtractResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const isDragging = useRef(false)
  const dragStart = useRef({ x: 0, y: 0 })
  const selectionRef = useRef<{ x: number; y: number; width: number; height: number } | null>(null)

  const handleFileSelect = useCallback(async (file: File) => {
    if (!file.type.startsWith('video/')) {
      setError('Please select a video file')
      return
    }

    setVideoFile(file)
    setError(null)
    setResult(null)
    
    const url = URL.createObjectURL(file)
    setVideoUrl(url)

    const video = document.createElement('video')
    video.src = url
    video.onloadedmetadata = () => {
      setVideoInfo({
        duration: video.duration,
        width: video.videoWidth,
        height: video.videoHeight
      })
      setDuration(video.duration)
      setEndTime(Math.min(video.duration, 300))
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFileSelect(file)
  }, [handleFileSelect])

  const handleUpload = async () => {
    if (!videoFile) return

    setIsProcessing(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', videoFile)

    try {
      const response = await axios.post(`${API_URL}/api/upload`, formData)
      setVideoInfo(response.data)
      setDuration(response.data.duration)
      setEndTime(Math.min(response.data.duration, 300))
      setUploadedFilename(response.data.filename)
      setIsUploaded(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleExtract = async () => {
    if (!uploadedFilename || !roi) {
      setError('Please select a video and subtitle area')
      return
    }

    setIsProcessing(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${API_URL}/api/extract`, {
        filename: uploadedFilename,
        start_time: startTime,
        end_time: endTime,
        frame_interval: frameInterval,
        roi: roi
      })
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Extraction failed')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return

    const canvas = canvasRef.current
    if (!canvas) return

    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height

    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY

    isDragging.current = true
    dragStart.current = { x, y }
    selectionRef.current = { x, y, width: 0, height: 0 }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current || !selectionRef.current) return

    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return

    const canvas = canvasRef.current
    if (!canvas) return

    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height

    const currentX = (e.clientX - rect.left) * scaleX
    const currentY = (e.clientY - rect.top) * scaleY

    const x = Math.min(dragStart.current.x, currentX)
    const y = Math.min(dragStart.current.y, currentY)
    const width = Math.abs(currentX - dragStart.current.x)
    const height = Math.abs(currentY - dragStart.current.y)

    selectionRef.current = { x, y, width, height }
    setRoi({ x: Math.round(x), y: Math.round(y), width: Math.round(width), height: Math.round(height) })

    drawCanvas()
  }

  const handleMouseUp = () => {
    isDragging.current = false
  }

  const drawCanvas = () => {
    const canvas = canvasRef.current
    const video = videoRef.current
    if (!canvas || !video) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    ctx.drawImage(video, 0, 0)

    if (selectionRef.current) {
      const { x, y, width, height } = selectionRef.current
      ctx.strokeStyle = '#00ff00'
      ctx.lineWidth = 3
      ctx.setLineDash([5, 5])
      ctx.strokeRect(x, y, width, height)
      ctx.fillStyle = 'rgba(0, 255, 0, 0.1)'
      ctx.fillRect(x, y, width, height)
    }
  }

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.addEventListener('timeupdate', () => {
        setCurrentTime(videoRef.current?.currentTime || 0)
      })
    }
  }, [])

  useEffect(() => {
    if (videoUrl && videoRef.current) {
      drawCanvas()
    }
  }, [videoUrl])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const downloadSRT = () => {
    if (!result?.srt_content) return

    const blob = new Blob([result.srt_content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const baseName = uploadedFilename?.replace(/\.[^/.]+$/, '') || 'subtitle'
    a.download = `${baseName}.srt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const copySRT = () => {
    if (!result?.srt_content) return
    navigator.clipboard.writeText(result.srt_content)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Video className="w-8 h-8 text-blue-600" />
            AI Subtitle Extractor
          </h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div 
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors"
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
            >
              <input
                type="file"
                accept="video/*"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                className="hidden"
                id="video-upload"
              />
              <label htmlFor="video-upload" className="cursor-pointer">
                <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600">Drag & drop a video file</p>
                <p className="text-gray-500 text-sm mt-1">or click to browse</p>
              </label>
            </div>

            {videoUrl && (
              <div className="bg-white rounded-lg shadow p-4">
                <div 
                  ref={containerRef}
                  className="relative bg-black rounded-lg overflow-hidden"
                  style={{ aspectRatio: '16/9' }}
                >
                  <video
                    ref={videoRef}
                    src={videoUrl}
                    className="w-full h-full object-contain"
                    onTimeUpdate={() => setCurrentTime(videoRef.current?.currentTime || 0)}
                  />
                  <canvas
                    ref={canvasRef}
                    className="absolute top-0 left-0 w-full h-full cursor-crosshair"
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                  />
                </div>

                <div className="flex items-center gap-4 mt-4">
                  <button
                    onClick={() => {
                      if (videoRef.current) {
                        if (isPlaying) videoRef.current.pause()
                        else videoRef.current.play()
                        setIsPlaying(!isPlaying)
                      }
                    }}
                    className="p-2 rounded-full bg-blue-600 text-white hover:bg-blue-700"
                  >
                    {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                  </button>
                  <span className="text-sm text-gray-600">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>
              </div>
            )}

            {roi && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  Selected Subtitle Area
                </h3>
                <div className="grid grid-cols-4 gap-2 text-sm">
                  <div>X: {roi.x}</div>
                  <div>Y: {roi.y}</div>
                  <div>W: {roi.width}</div>
                  <div>H: {roi.height}</div>
                </div>
                <button
                  onClick={() => {
                    setRoi(null)
                    selectionRef.current = null
                    drawCanvas()
                  }}
                  className="mt-2 text-red-600 hover:text-red-700 text-sm flex items-center gap-1"
                >
                  <Trash2 className="w-4 h-4" /> Clear selection
                </button>
              </div>
            )}
          </div>

          <div className="space-y-6">
            {videoInfo && (
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-medium text-gray-900 mb-4">Settings</h3>
                
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">Start Time (s)</label>
                    <input
                      type="number"
                      min="0"
                      max={duration}
                      value={startTime}
                      onChange={(e) => setStartTime(Number(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">End Time (s)</label>
                    <input
                      type="number"
                      min={startTime}
                      max={duration}
                      value={endTime}
                      onChange={(e) => setEndTime(Number(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-sm text-gray-600 mb-1">Frame Interval (seconds)</label>
                  <input
                    type="number"
                    min="0.5"
                    max="10"
                    step="0.5"
                    value={frameInterval}
                    onChange={(e) => setFrameInterval(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                {!isUploaded ? (
                  <button
                    onClick={handleUpload}
                    disabled={!videoFile || isProcessing}
                    className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isProcessing ? 'Uploading...' : 'Upload Video'}
                  </button>
                ) : (
                  <button
                    onClick={handleExtract}
                    disabled={!roi || isProcessing}
                    className="w-full py-2 px-4 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    {isProcessing ? 'Processing...' : 'Extract Subtitles'}
                  </button>
                )}
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
                {error}
              </div>
            )}

            {result && (
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium text-gray-900">Result</h3>
                  <div className="flex gap-2">
                    <button
                      onClick={downloadSRT}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                      title="Download SRT"
                    >
                      <Download className="w-5 h-5" />
                    </button>
                    <button
                      onClick={copySRT}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                      title="Copy to clipboard"
                    >
                      <Copy className="w-5 h-5" />
                    </button>
                  </div>
                </div>
                
                <div className="text-sm text-gray-600 mb-4">
                  Processing time: {result.processing_time}s
                </div>

                <textarea
                  readOnly
                  value={result.srt_content || 'No subtitles extracted'}
                  className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
                />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
