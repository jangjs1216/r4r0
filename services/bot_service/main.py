from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from models import (
    Base, engine, SessionLocal, 
    Bot, BotCreate, BotUpdate, BotResponse, bot_to_pydantic,
    LocalOrder, LocalOrderCreate, LocalOrderResponse, OrderStatusUpdate,
    GlobalExecution, GlobalExecutionCreate
)

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BotService", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        if "," in status:
            statuses = status.split(",")
            query = query.filter(Bot.status.in_(statuses))
        else:
            query = query.filter(Bot.status == status)
    bots = query.offset(skip).limit(limit).all()
    return [bot_to_pydantic(bot) for bot in bots]

@app.get("/bots/{bot_id}", response_model=BotResponse)
def read_bot(bot_id: str, db: Session = Depends(get_db)):
    db_bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if db_bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot_to_pydantic(db_bot)

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

@app.get("/bots/{bot_id}/position")
def get_bot_position(bot_id: str, db: Session = Depends(get_db)):
    """Calculate Net Position based on Global Executions."""
    executions = db.query(GlobalExecution).join(LocalOrder).filter(LocalOrder.bot_id == bot_id).all()
    
    net_qty = 0.0
    symbol = "UNKNOWN"
    
    for exc in executions:
        symbol = exc.symbol # Assume single symbol for now (or last traded)
        
        # If side is available (New Schema), use it.
        # Fallback to LocalOrder side if missing (Old Schema).
        side = exc.side
        if not side and exc.local_order:
            side = exc.local_order.side
            
        if side == "BUY":
            net_qty += exc.quantity
        elif side == "SELL":
            net_qty -= exc.quantity
            
    # Round to avoid float precision issues
    net_qty = round(net_qty, 8)
    
    return {
        "bot_id": bot_id,
        "symbol": symbol,
        "net_quantity": net_qty
    }

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
        side=exec_in.side,
        price=exec_in.price,
        quantity=exec_in.quantity,
        fee=exec_in.fee,
        fee_currency=exec_in.fee_currency,
        realized_pnl=exec_in.realized_pnl,
        position_side=exec_in.position_side,
        raw_response=exec_in.raw_response,
        timestamp=exec_in.timestamp
    )
    
    try:
        db.add(db_exec)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to record execution: {str(e)}")
        
    return {"ok": True}

# --- Trades API (Performance View) ---

class ExecutionDetail(BaseModel):
    exchange_trade_id: str
    side: str
    price: float
    quantity: float
    fee: float
    fee_currency: Optional[str]
    realized_pnl: Optional[float]
    timestamp: datetime

class TradeRecord(BaseModel):
    local_order_id: str
    bot_id: str
    bot_name: str
    symbol: str
    side: str
    intent_quantity: float
    intent_time: datetime
    status: str
    reason: Optional[str]
    execution: Optional[ExecutionDetail]

class BotPerformance(BaseModel):
    bot_id: str
    bot_name: str
    total_trades: int
    filled_trades: int
    total_pnl: float
    total_fees: float
    win_count: int
    loss_count: int
    win_rate: float

class TradesResponse(BaseModel):
    trades: List[TradeRecord]
    bot_performances: List[BotPerformance]
    summary: dict

@app.get("/trades", response_model=TradesResponse)
def get_trades(
    bot_id: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    db: Session = Depends(get_db)
):
    """Get trades with bot-level performance aggregation."""
    
    # Build query
    query = db.query(LocalOrder)
    if bot_id:
        query = query.filter(LocalOrder.bot_id == bot_id)
    if symbol:
        query = query.filter(LocalOrder.symbol == symbol)
    if from_date:
        query = query.filter(LocalOrder.timestamp >= from_date)
    if to_date:
        query = query.filter(LocalOrder.timestamp <= to_date)
    
    orders = query.order_by(LocalOrder.timestamp.desc()).all()
    
    # Aggregate by bot
    bot_stats = {}  # bot_id -> stats
    trades = []
    total_pnl = 0.0
    total_fees = 0.0
    
    for order in orders:
        bot = db.query(Bot).filter(Bot.id == order.bot_id).first()
        bot_name = bot.name if bot else "Unknown"
        
        # Initialize bot stats
        if order.bot_id not in bot_stats:
            bot_stats[order.bot_id] = {
                "bot_name": bot_name,
                "total_trades": 0,
                "filled_trades": 0,
                "total_pnl": 0.0,
                "total_fees": 0.0,
                "win_count": 0,
                "loss_count": 0
            }
        
        stats = bot_stats[order.bot_id]
        stats["total_trades"] += 1
        
        # Get execution
        exec_record = db.query(GlobalExecution).filter(
            GlobalExecution.local_order_id == order.id
        ).first()
        
        execution_detail = None
        if exec_record:
            execution_detail = ExecutionDetail(
                exchange_trade_id=exec_record.id,
                side=exec_record.side or order.side,
                price=exec_record.price,
                quantity=exec_record.quantity,
                fee=exec_record.fee,
                fee_currency=exec_record.fee_currency,
                realized_pnl=exec_record.realized_pnl,
                timestamp=exec_record.timestamp
            )
            
            stats["filled_trades"] += 1
            stats["total_fees"] += exec_record.fee or 0
            total_fees += exec_record.fee or 0
            
            # PnL tracking
            if exec_record.realized_pnl is not None:
                stats["total_pnl"] += exec_record.realized_pnl
                total_pnl += exec_record.realized_pnl
                if exec_record.realized_pnl >= 0:
                    stats["win_count"] += 1
                else:
                    stats["loss_count"] += 1
            else:
                # Simple tracking: SELL = profit taken, BUY = cost
                trade_value = exec_record.price * exec_record.quantity
                if order.side == "SELL":
                    stats["win_count"] += 1
                else:
                    pass  # BUY is entry, not profit yet
        
        trades.append(TradeRecord(
            local_order_id=order.id,
            bot_id=order.bot_id,
            bot_name=bot_name,
            symbol=order.symbol,
            side=order.side,
            intent_quantity=order.quantity,
            intent_time=order.timestamp,
            status=order.status,
            reason=order.reason,
            execution=execution_detail
        ))
    
    # Build bot performances list
    bot_performances = []
    for bid, stats in bot_stats.items():
        filled = stats["filled_trades"]
        win_rate = (stats["win_count"] / filled * 100) if filled > 0 else 0.0
        bot_performances.append(BotPerformance(
            bot_id=bid,
            bot_name=stats["bot_name"],
            total_trades=stats["total_trades"],
            filled_trades=filled,
            total_pnl=round(stats["total_pnl"], 4),
            total_fees=round(stats["total_fees"], 4),
            win_count=stats["win_count"],
            loss_count=stats["loss_count"],
            win_rate=round(win_rate, 2)
        ))
    
    summary = {
        "total_trades": len(trades),
        "total_pnl": round(total_pnl, 4),
        "total_fees": round(total_fees, 4),
        "bot_count": len(bot_stats)
    }
    
    return TradesResponse(trades=trades, bot_performances=bot_performances, summary=summary)
