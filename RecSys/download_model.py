from sentence_transformers import CrossEncoder
import torch
import os

model_name = "BAAI/bge-reranker-v2-m3"
print(f"Pre-downloading model: {model_name}...")

# Force download even if not on GPU during build
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CrossEncoder(model_name, device=device)

print("Model downloaded successfully.")
