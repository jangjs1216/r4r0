# Development & Deployment Guide

## 1. Local Development (Manual)
소스 코드를 수정하고 즉시 반영(Hot Reload)되는 환경이 필요할 때 사용합니다.

### Backend (AuthService)
```bash
cd services/auth

# Create Virtual Environment (First time only)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run Server
export MASTER_KEY="dev_key_12345"
uvicorn services.auth.main:app --reload --port 8000
```
- API Docs: http://localhost:8000/docs
- Key DB: `data/auth.db` (SQLite)

### Frontend (Console)
```bash
cd frontend
npm install
npm run dev
```
- Web UI: http://localhost:5173
- 프록시가 없으므로 `AuthView.tsx`는 `http://localhost:8000`을 직접 호출합니다 (CORS 허용됨).

---

## 2. Docker Deployment (Integrated)
실제 운영 환경과 유사하게, 단일 엔드포인트에서 모든 서비스를 실행할 때 사용합니다.

### Prerequisites
- Docker & Docker Compose installed

### Run
```bash
# 1. Set Encryption Key (Important!)
export MASTER_KEY="your-secure-production-key-change-this"

# 2. Build & Run
docker-compose up --build
```
- Web UI: http://localhost (Port 80)
- Nginx가 정적 파일을 서빙하고, `/api/*` 요청을 백엔드 컨테이너로 라우팅합니다.

### Container Structure
- **frontend**: React Build Files + Nginx (Reverse Proxy)
- **auth-service**: Python FastAPI (Port 8000 -> Internal)
- **Network**: `r4r0-net` (Bridge)
- **Volume**: `./data:/app/data` (DB 영속석 보장)
