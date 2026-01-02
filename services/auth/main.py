from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

# Local imports
from .database import SessionLocal, init_db, StoredCredential
from .crypto import encrypt_secret, decrypt_secret

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AuthService (Key Manager)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 프로덕션 환경에서는 프론트엔드 도메인으로 제한해야 함
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependencies ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models ---
class RegisterKeyRequest(BaseModel):
    exchange: str
    label: str
    publicKey: str
    secretKey: str

class ExchangeKeySummary(BaseModel):
    id: str
    exchange: str
    label: str
    publicKeyMasked: str
    status: str
    permissions: List[str]
    createdAt: datetime

    class Config:
        from_attributes = True

# --- Helpers ---
def mask_key(key: str) -> str:
    if len(key) < 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"

# --- Lifecycle ---
@app.on_event("startup")
def on_startup():
    init_db()

# --- Routes ---
@app.get("/keys", response_model=List[ExchangeKeySummary])
def list_keys(db: Session = Depends(get_db)):
    creds = db.query(StoredCredential).all()
    results = []
    for c in creds:
        results.append(ExchangeKeySummary(
            id=c.id,
            exchange=c.exchange,
            label=c.label,
            publicKeyMasked=mask_key(c.public_key),
            status=c.status,
            permissions=["read", "trade"], # 현재는 모의 권한(Mock)
            createdAt=c.created_at
        ))
    return results

@app.post("/keys", status_code=status.HTTP_201_CREATED, response_model=ExchangeKeySummary)
def register_key(req: RegisterKeyRequest, db: Session = Depends(get_db)):
    # 비밀 키 암호화
    enc_secret = encrypt_secret(req.secretKey)
    
    new_cred = StoredCredential(
        id=str(uuid.uuid4()),
        exchange=req.exchange,
        label=req.label,
        public_key=req.publicKey,
        secret_key_enc=enc_secret,
        status="active"
    )
    
    db.add(new_cred)
    db.commit()
    db.refresh(new_cred)
    
    return ExchangeKeySummary(
        id=new_cred.id,
        exchange=new_cred.exchange,
        label=new_cred.label,
        publicKeyMasked=mask_key(new_cred.public_key),
        status=new_cred.status,
        permissions=["read", "trade"],
        createdAt=new_cred.created_at
    )

@app.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_key(key_id: str, db: Session = Depends(get_db)):
    cred = db.query(StoredCredential).filter(StoredCredential.id == key_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Key not found")
    
    db.delete(cred)
    db.commit()
    return

# --- 내부 API (마이크로서비스 전용) ---
# 프로덕션에서는 네트워크 정책이나 내부 인증 토큰으로 접근을 제한해야 함
class InternalKeyResponse(BaseModel):
    exchange: str
    publicKey: str
    secretKey: str
    passphrase: Optional[str] = None

@app.get("/internal/keys/{key_id}/secret", response_model=InternalKeyResponse)
def get_decrypted_key(key_id: str, db: Session = Depends(get_db)):
    cred = db.query(StoredCredential).filter(StoredCredential.id == key_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Key not found")
    
    decrypted_secret = decrypt_secret(cred.secret_key_enc)
    
    return InternalKeyResponse(
        exchange=cred.exchange,
        publicKey=cred.public_key,
        secretKey=decrypted_secret
    )

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auth-service"}
