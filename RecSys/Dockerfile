# Use PyTorch's official CUDA-enabled runtime image (Updated to 2.5.1 for 2026 compatibility)
FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

# Set working directory
WORKDIR /app

# Copy requirements and install
# Note: we use --no-cache-dir to keep the image size small
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Pre-download the ML model to ensure instant startup
RUN python download_model.py

# Expose port (HTTP default)
EXPOSE 80

# Command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
