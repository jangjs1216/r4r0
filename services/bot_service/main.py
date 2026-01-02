from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from models import (
    Base, engine, SessionLocal, 
    Bot, BotCreate, BotUpdate, BotResponse, bot_to_pydantic,
    LocalOrder, LocalOrderCreate, LocalOrderResponse, OrderStatusUpdate,
    GlobalExecution, GlobalExecutionCreate, BotStatsResponse
)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BotService", version="1.0.0")

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

def match_fifo_orders(db: Session, sell_exec: GlobalExecution, bot_id: str):
    """
    FIFO Matching Engine with Bot Isolation.
    Matches a SELL execution against open BUY lots for the specific bot.
    Updates 'remaining_qty' of BUY lots and calculates 'realized_pnl' for the SELL.
    """
    if sell_exec.side != "SELL":
        return

    # 1. Fetch Open BUY Lots (Isolated by Bot ID)
    # Ordered by Timestamp ASC (FIFO)
    buy_lots = db.query(GlobalExecution).join(LocalOrder).filter(
        GlobalExecution.symbol == sell_exec.symbol,
        GlobalExecution.side == "BUY",
        GlobalExecution.remaining_qty > 0,
        LocalOrder.bot_id == bot_id
    ).order_by(GlobalExecution.timestamp.asc()).all()

    sell_qty_remain = sell_exec.quantity
    total_pnl = 0.0

    print(f"[PnL] Matching SELL {sell_exec.id} (Qty: {sell_qty_remain}) for Bot {bot_id}")

    for buy_lot in buy_lots:
        if sell_qty_remain <= 0:
            break
        
        # Determine match quantity
        match_qty = min(buy_lot.remaining_qty, sell_qty_remain)
        
        # Calculate Gross PnL for this chunk
        # (Sell Price - Buy Price) * Match Qty
        pnl_chunk = (sell_exec.price - buy_lot.price) * match_qty
        total_pnl += pnl_chunk
        
        # Update Buy Lot State
        buy_lot.remaining_qty -= match_qty
        
        # Update Sell logic
        sell_qty_remain -= match_qty

        print(f"  -> Matched {match_qty} from BUY {buy_lot.id} | PnL Chunk: {pnl_chunk:.2f}")

    # 2. Update SELL Execution Result
    sell_exec.realized_pnl = total_pnl
    # Note: sell_exec.remaining_qty defaults to 0, which is correct for SELLs (unless shorting)
    
    print(f"[PnL] Result: Total Realized PnL = {total_pnl:.2f}, Unmatched Qty = {sell_qty_remain}")


@app.post("/executions")
def record_execution(exec_in: GlobalExecutionCreate, db: Session = Depends(get_db)):
    print(f"[BotService] Recording Execution: TradeID={exec_in.exchange_trade_id}, Side={exec_in.side}")
    
    # Check if Local Order exists and get Bot ID (For Isolation)
    db_order = db.query(LocalOrder).filter(LocalOrder.id == exec_in.local_order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Local Order not found")
    
    # Create Execution Entity with FULL fields
    db_exec = GlobalExecution(
        id=exec_in.exchange_trade_id,
        local_order_id=exec_in.local_order_id,
        exchange_order_id=exec_in.exchange_order_id,
        order_list_id=exec_in.order_list_id,
        symbol=exec_in.symbol,
        side=exec_in.side,
        price=exec_in.price,
        quantity=exec_in.quantity,
        quote_qty=exec_in.quote_qty,
        fee=exec_in.fee,
        fee_asset=exec_in.fee_asset,
        timestamp=exec_in.timestamp,
        remaining_qty=0.0, # Default
        realized_pnl=0.0   # Default
    )
    
    # Logic: Set Remaining Qty for BUY or Run Matching for SELL
    if db_exec.side == "BUY":
        db_exec.remaining_qty = db_exec.quantity
    elif db_exec.side == "SELL":
        match_fifo_orders(db, db_exec, db_order.bot_id)
    
    try:
        db.add(db_exec)
        db.commit()
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to record execution: {str(e)}")
        
    return {"ok": True, "realized_pnl": db_exec.realized_pnl}

@app.get("/bots/{bot_id}/stats", response_model=BotStatsResponse)
def get_bot_stats(bot_id: str, db: Session = Depends(get_db)):
    """
    Calculate aggregated statistics for a specific bot.
    Stats are derived from realized PnL of SELL executions.
    """
    print(f"[BotService] Calculating Stats for Bot: {bot_id}")
    
    # 1. Fetch all SELL executions for this bot (completed trades)
    sell_execs = db.query(GlobalExecution).join(LocalOrder).filter(
        LocalOrder.bot_id == bot_id,
        GlobalExecution.side == "SELL"
    ).all()

    total_pnl = 0.0
    wins = 0
    total_trades = len(sell_execs)
    gross_profit = 0.0
    gross_loss = 0.0

    for exc in sell_execs:
        pnl = exc.realized_pnl
        total_pnl += pnl
        
        if pnl > 0:
            wins += 1
            gross_profit += pnl
        else:
            gross_loss += abs(pnl) # Absolute value for PF calculation

    win_rate = (wins / total_trades) if total_trades > 0 else 0.0
    average_pnl = (total_pnl / total_trades) if total_trades > 0 else 0.0
    
    # Profit Factor: Gross Profit / Gross Loss
    if gross_loss == 0:
        profit_factor = float('inf') if gross_profit > 0 else 0.0
    else:
        profit_factor = gross_profit / gross_loss

    return BotStatsResponse(
        total_pnl=total_pnl,
        win_rate=win_rate,
        total_trades=total_trades,
        profit_factor=profit_factor,
        average_pnl=average_pnl
    )
