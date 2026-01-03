from sqlalchemy import Column, String, Text, DateTime, create_engine, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import json
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

import os

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bots.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Models ---
class Bot(Base):
    __tablename__ = "bots"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    status = Column(String, default="STOPPED") # STOPPED, BOOTING, RUNNING, STOPPING
    status_message = Column(String, nullable=True) # UI 표시용 상태 메시지
    config_json = Column(Text) # 전체 JSON 설정 저장
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_config(self, config_dict):
        self.config_json = json.dumps(config_dict)

    def get_config(self):
        return json.loads(self.config_json) if self.config_json else {}

    orders = relationship("LocalOrder", back_populates="bot", cascade="all, delete-orphan")
    sessions = relationship("BotSession", back_populates="bot", cascade="all, delete-orphan")

class BotSession(Base):
    """
    봇의 실행 주기(세션)를 관리하는 모델.
    Start ~ Stop 사이의 기간을 하나의 세션으로 정의하며, PnL 집계의 기준이 됨.
    """
    __tablename__ = "bot_sessions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    bot_id = Column(String, ForeignKey("bots.id"), index=True)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True) # 실행 중일 땐 Null
    status = Column(String, default="ACTIVE") # ACTIVE, ENDED, CRASHED
    
    # 세션 요약 정보 (JSON 캐싱) - 실시간 계산 부하를 줄이기 위함
    # 예: {"total_pnl": 10.5, "win_rate": 0.6, "total_trades": 5}
    summary_json = Column(Text, default="{}")

    bot = relationship("Bot", back_populates="sessions")
    orders = relationship("LocalOrder", back_populates="session")

    def set_summary(self, summary_dict):
        self.summary_json = json.dumps(summary_dict)

    def get_summary(self):
        return json.loads(self.summary_json) if self.summary_json else {}

class LocalOrder(Base):
    __tablename__ = "local_orders"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    bot_id = Column(String, ForeignKey("bots.id"), index=True)
    session_id = Column(String, ForeignKey("bot_sessions.id"), index=True, nullable=True) # 초기엔 Nullable (Migration용)
    
    symbol = Column(String)
    side = Column(String)     # BUY, SELL
    quantity = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="PENDING") # PENDING, SENT, FILLED, FAILED
    reason = Column(String, nullable=True) # 주문 사유 (예: "RSI < 30")

    bot = relationship("Bot", back_populates="orders")
    session = relationship("BotSession", back_populates="orders")
    executions = relationship("GlobalExecution", back_populates="local_order")

class GlobalExecution(Base):
    __tablename__ = "global_executions"

    id = Column(String, primary_key=True) # Exchange Trade ID
    local_order_id = Column(String, ForeignKey("local_orders.id"), index=True)
    exchange_order_id = Column(String, index=True) # Exchange Order ID
    order_list_id = Column(String, nullable=True)  # OCO Group ID
    symbol = Column(String)
    side = Column(String) # BUY / SELL
    price = Column(Float)
    quantity = Column(Float)
    quote_qty = Column(Float) # Price * Quantity
    fee = Column(Float, default=0.0)
    fee_asset = Column(String, nullable=True)
    timestamp = Column(DateTime) # 거래소 체결 시간
    
    # PnL(손익) 추적용 필드
    remaining_qty = Column(Float, default=0.0) # FIFO 매칭을 위한 잔여 수량
    realized_pnl = Column(Float, default=0.0)  # 성과 추적을 위한 실현 손익

    local_order = relationship("LocalOrder", back_populates="executions")


# --- Pydantic Schemas ---

class BotBase(BaseModel):
    name: str
    status: str = "STOPPED"  # STOPPED, BOOTING, RUNNING, STOPPING
    status_message: Optional[str] = None
    global_settings: Dict[str, Any] = {}
    pipeline: Dict[str, Any] = {}

class BotCreate(BotBase):
    pass

class BotUpdate(BotBase):
    pass

class BotResponse(BotBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Ledger Schemas
class LocalOrderCreate(BaseModel):
    bot_id: str
    symbol: str
    side: str
    quantity: float
    reason: Optional[str] = None
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = None

class LocalOrderResponse(BaseModel):
    id: str
    bot_id: str
    session_id: Optional[str] = None
    symbol: str
    side: str
    quantity: float
    timestamp: datetime
    status: str
    reason: Optional[str] = None

    class Config:
        from_attributes = True

class BotSessionResponse(BaseModel):
    id: str
    bot_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    summary: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class BotSessionDetailResponse(BotSessionResponse):
    orders: List[LocalOrderResponse] = []

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str

class GlobalExecutionCreate(BaseModel):
    local_order_id: str
    exchange_trade_id: str
    exchange_order_id: str
    order_list_id: Optional[str] = None
    symbol: str
    side: str
    price: float
    quantity: float
    quote_qty: float
    fee: float = 0.0
    fee_asset: Optional[str] = None
    timestamp: datetime

# DB 엔티티를 Pydantic 모델로 변환하는 헬퍼 함수
def bot_to_pydantic(bot: Bot) -> BotResponse:
    config = bot.get_config()
    return BotResponse(
        id=bot.id,
        name=bot.name,
        status=bot.status,
        status_message=bot.status_message,
        global_settings=config.get("global_settings", {}),
        pipeline=config.get("pipeline", {}),
        created_at=bot.created_at,
        updated_at=bot.updated_at
    )

# --- 통계(Stats) 스키마 ---
class BotStatsResponse(BaseModel):
    total_pnl: float
    win_rate: float
    total_trades: int
    profit_factor: Optional[float]
    average_pnl: float
