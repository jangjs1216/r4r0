from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from models import (
    Base, engine, SessionLocal, 
    Bot, BotCreate, BotUpdate, BotResponse, bot_to_pydantic,
    LocalOrder, LocalOrderCreate, LocalOrderResponse, OrderStatusUpdate,
    GlobalExecution, GlobalExecutionCreate
)

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
def read_bots(skip: int = 0, limit: int = 100, status: str = None, db: Session = Depends(get_db)):
    query = db.query(Bot)
    if status:
        query = query.filter(Bot.status == status)
    bots = query.offset(skip).limit(limit).all()
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

# --- Ledger APIs ---

@app.post("/orders", response_model=LocalOrderResponse)
def create_local_order(order_in: LocalOrderCreate, db: Session = Depends(get_db)):
    print(f"[BotService] Received Local Order: {order_in.symbol} {order_in.side} ({order_in.reason})")
    db_order = LocalOrder(
        bot_id=order_in.bot_id,
        symbol=order_in.symbol,
        side=order_in.side,
        quantity=order_in.quantity,
        reason=order_in.reason,
        timestamp=order_in.timestamp
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return LocalOrderResponse(id=db_order.id, status=db_order.status)

@app.put("/orders/{order_id}/status", response_model=LocalOrderResponse)
def update_order_status(order_id: str, status_update: OrderStatusUpdate, db: Session = Depends(get_db)):
    print(f"[BotService] Updating Status: {order_id} -> {status_update.status}")
    db_order = db.query(LocalOrder).filter(LocalOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Local Order not found")
    
    db_order.status = status_update.status
    db.commit()
    return LocalOrderResponse(id=db_order.id, status=db_order.status)

@app.post("/executions")
def record_execution(exec_in: GlobalExecutionCreate, db: Session = Depends(get_db)):
    print(f"[BotService] Recording Execution: TradeID={exec_in.exchange_trade_id}")
    # Check if Local Order exists
    db_order = db.query(LocalOrder).filter(LocalOrder.id == exec_in.local_order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Local Order not found")
    
    db_exec = GlobalExecution(
        id=exec_in.exchange_trade_id,
        local_order_id=exec_in.local_order_id,
        exchange_order_id=exec_in.exchange_order_id,
        position_id=exec_in.position_id,
        symbol=exec_in.symbol,
        price=exec_in.price,
        quantity=exec_in.quantity,
        fee=exec_in.fee,
        timestamp=exec_in.timestamp
    )
    
    try:
        db.add(db_exec)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to record execution: {str(e)}")
        
    return {"ok": True}
