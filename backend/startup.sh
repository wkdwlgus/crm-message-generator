#!/bin/bash
# Azure App Service(Linux)용 FastAPI 시작 스크립트

# 1. 의존성 설치 (필요시)
# pip install -r requirements.txt

# 2. Gunicorn을 사용하여 Uvicorn 워커 실행
# --bind: Azure App Service는 서버의 80번 포트를 8000번 포트로 브릿징함
# --workers: 리소스에 맞게 조절 (기본 2~4)
# --worker-class: uvicorn 워커 사용
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 600
