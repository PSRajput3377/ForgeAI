#!/usr/bin/env bash
# Pull the Ollama models ForgeAI uses. Large download (~15-20GB); run once.
# Requires the ollama service to be running:  make up
set -euo pipefail

MODELS=(
  "qwen3:8b"            # Planning & reasoning
  "deepseek-coder"     # Code generation
  "llama3.1:8b"        # Research & summaries
  "nomic-embed-text"   # Embeddings for RAG
)

echo "Pulling ${#MODELS[@]} models into the forge-ollama container..."
for model in "${MODELS[@]}"; do
  echo "==> $model"
  docker exec forge-ollama ollama pull "$model"
done

echo "Done. Installed models:"
docker exec forge-ollama ollama list
