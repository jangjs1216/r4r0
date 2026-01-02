from sqlalchemy import Column, String, Text, DateTime, create_engine, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import json
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

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
    status = Column(String, default="STOPPED")
    config_json = Column(Text) # Stores the full JSON config
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_config(self, config_dict):
        self.config_json = json.dumps(config_dict)

    def get_config(self):
        return json.loads(self.config_json) if self.config_json else {}

class LocalOrder(Base):
    __tablename__ = "local_orders"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    bot_id = Column(String, ForeignKey("bots.id"), index=True)
    symbol = Column(String)
    side = Column(String)     # BUY, SELL
    quantity = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="PENDING") # PENDING, SENT, FILLED, FAILED
    reason = Column(String, nullable=True) # Reason for the order (e.g. "RSI < 30")

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
    timestamp = Column(DateTime) # Exchange Time
    
    # PnL Tracking
    remaining_qty = Column(Float, default=0.0) # For FIFO Matching
    realized_pnl = Column(Float, default=0.0)  # For Performance Tracking

    local_order = relationship("LocalOrder", back_populates="executions")


# --- Pydantic Schemas ---

class BotBase(BaseModel):
    name: str
    status: str = "STOPPED"
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

class LocalOrderResponse(BaseModel):
    id: str
    status: str

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

# Helper to reconstruct Pydantic model from DB entity
def bot_to_pydantic(bot: Bot) -> BotResponse:
    config = bot.get_config()
    return BotResponse(
        id=bot.id,
        name=bot.name,
        status=bot.status,
        global_settings=config.get("global_settings", {}),
        pipeline=config.get("pipeline", {}),
        created_at=bot.created_at,
        updated_at=bot.updated_at
    )
