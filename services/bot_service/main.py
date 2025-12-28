from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from models import Base, engine, SessionLocal, Bot, BotCreate, BotUpdate, BotResponse, bot_to_pydantic

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BotService", version="1.0.0")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/bots", response_model=List[BotResponse])
def read_bots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    bots = db.query(Bot).offset(skip).limit(limit).all()
    return [bot_to_pydantic(bot) for bot in bots]

@app.post("/bots", response_model=BotResponse)
def create_bot(bot_in: BotCreate, db: Session = Depends(get_db)):
    # Serialize config parts to JSON storage
    config_dict = {
        "global_settings": bot_in.global_settings,
        "pipeline": bot_in.pipeline
    }
    
    db_bot = Bot(
        name=bot_in.name,
        status=bot_in.status
    )
    db_bot.set_config(config_dict)
    
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return bot_to_pydantic(db_bot)

@app.get("/bots/{bot_id}", response_model=BotResponse)
def read_bot(bot_id: str, db: Session = Depends(get_db)):
    db_bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if db_bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot_to_pydantic(db_bot)

@app.put("/bots/{bot_id}", response_model=BotResponse)
def update_bot(bot_id: str, bot_in: BotUpdate, db: Session = Depends(get_db)):
    db_bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if db_bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")

    db_bot.name = bot_in.name
    db_bot.status = bot_in.status
    
    config_dict = {
        "global_settings": bot_in.global_settings,
        "pipeline": bot_in.pipeline
    }
    db_bot.set_config(config_dict)

    db.commit()
    db.refresh(db_bot)
    return bot_to_pydantic(db_bot)

@app.delete("/bots/{bot_id}")
def delete_bot(bot_id: str, db: Session = Depends(get_db)):
    db_bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if db_bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    db.delete(db_bot)
    db.commit()
    return {"ok": True}
