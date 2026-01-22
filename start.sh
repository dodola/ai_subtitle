#!/bin/bash

echo "=========================================="
echo "AI Subtitle Extractor - Startup Script"
echo "=========================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
	echo "Error: Docker is not running"
	exit 1
fi

# Check if Ollama is running on host
if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
	echo "Warning: Ollama is not running on localhost:11434"
	echo "Please start Ollama first:"
	echo "  1. Install: curl -fsSL https://ollama.ai/install.sh | sh"
	echo "  2. Start: ollama serve"
	echo "  3. Pull model: ollama pull qwen2-vl"
	echo ""
	read -p "Continue anyway? (y/n) " -n 1 -r
	echo
	if [[ ! $REPLY =~ ^[Yy]$ ]]; then
		exit 1
	fi
fi

# Start services
echo "Starting services..."
docker compose up -d

echo ""
echo "=========================================="
echo "Services started:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  Ollama:   http://localhost:11434 (host)"
echo "=========================================="
