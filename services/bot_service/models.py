from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
