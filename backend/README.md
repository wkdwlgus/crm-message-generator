# Backend

FastAPI 기반 백엔드 서버입니다.

## 설치 방법

1. 가상환경 생성:
```bash
python -m venv venv
```

2. 가상환경 활성화:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

## 실행 방법

```bash
uvicorn main:app --reload --port 8000
```

서버는 http://localhost:8000 에서 실행됩니다.

API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다.
