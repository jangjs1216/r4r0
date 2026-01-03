from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from models import (
    Base, engine, SessionLocal, 
    Bot, BotCreate, BotUpdate, BotResponse, bot_to_pydantic,
    LocalOrder, LocalOrderCreate, LocalOrderResponse, OrderStatusUpdate,
    GlobalExecution, GlobalExecutionCreate, BotStatsResponse,
    BotSession, BotSessionResponse, BotSessionDetailResponse
)
from datetime import datetime
import json
import uuid
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BotService", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:5173", "http://127.0.0.1", "http://localhost:80", "http://localhost:3000"],
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
    # 설정(Config) 데이터를 JSON 저장용 딕셔너리로 직렬화
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

    db.delete(db_bot)
    db.commit()
    return {"ok": True}

# --- Session APIs ---

@app.post("/bots/{bot_id}/start", response_model=BotSessionResponse)
def start_bot_session(bot_id: str, db: Session = Depends(get_db)):
    db_bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not db_bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # 1. Close existing active session if any
    active_session = db.query(BotSession).filter(
        BotSession.bot_id == bot_id, 
        BotSession.status == "ACTIVE"
    ).first()
    
    if active_session:
        print(f"[Session] Closing stale active session {active_session.id} for bot {bot_id}")
        active_session.end_time = datetime.utcnow()
        active_session.status = "ENDED"
    
    # 2. Create new session
    new_session = BotSession(
        bot_id=bot_id,
        status="ACTIVE",
        start_time=datetime.utcnow()
    )
    db.add(new_session)
    
    # 3. Update Bot Status
    db_bot.status = "RUNNING"
    
    db.commit()
    db.refresh(new_session)
    db.refresh(db_bot)
    
    return new_session

@app.post("/bots/{bot_id}/stop", response_model=BotSessionResponse)
def stop_bot_session(bot_id: str, db: Session = Depends(get_db)):
    db_bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not db_bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # 1. Find Active Session
    active_session = db.query(BotSession).filter(
        BotSession.bot_id == bot_id, 
        BotSession.status == "ACTIVE"
    ).first()
    
    if active_session:
        active_session.end_time = datetime.utcnow()
        active_session.status = "ENDED"
    else:
        # No active session found to stop, create a dummy ended one or just return error?
        # We'll just return a dummy response or raise error. 
        # But to be safe let's check if we recently stopped it.
        # Just return the latest session if possible or raise 404
        pass

    # 2. Update Bot Status
    db_bot.status = "STOPPED"
    
    db.commit()
    if active_session:
        db.refresh(active_session)
        return active_session
    else:
        # Fallback if no active session was found (e.g. force stopped)
        raise HTTPException(status_code=400, detail="No active session found to stop")

@app.get("/bots/{bot_id}/sessions", response_model=List[BotSessionResponse])
def get_bot_sessions(bot_id: str, db: Session = Depends(get_db)):
    sessions = db.query(BotSession).filter(BotSession.bot_id == bot_id).order_by(BotSession.start_time.desc()).all()
    # Add summary dict to response
    results = []
    for s in sessions:
        resp = BotSessionResponse.from_orm(s)
        resp.summary = s.get_summary()
        results.append(resp)
    return results

@app.get("/sessions/{session_id}", response_model=BotSessionDetailResponse)
def get_session_detail(session_id: str, db: Session = Depends(get_db)):
    s = db.query(BotSession).filter(BotSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    resp = BotSessionDetailResponse.from_orm(s)
    resp.summary = s.get_summary()
    return resp

# --- Ledger APIs ---

@app.post("/orders", response_model=LocalOrderResponse)
def create_local_order(order_in: LocalOrderCreate, db: Session = Depends(get_db)):
    print(f"[BotService] Received Local Order: {order_in.symbol} {order_in.side} ({order_in.reason})")
    
    # Session Linking Logic
    session_id = order_in.session_id
    if not session_id:
        # Auto-detect active session
        active_session = db.query(BotSession).filter(
            BotSession.bot_id == order_in.bot_id,
            BotSession.status == "ACTIVE"
        ).order_by(BotSession.start_time.desc()).first()
        
        if active_session:
            session_id = active_session.id
        else:
            print(f"[WARN] No active session found for bot {order_in.bot_id}. Creating emergency session.")
            emerg_session = BotSession(bot_id=order_in.bot_id, status="ACTIVE", start_time=datetime.utcnow())
            db.add(emerg_session)
            db.commit() # Need ID
            db.refresh(emerg_session)
            session_id = emerg_session.id

    db_order = LocalOrder(
        bot_id=order_in.bot_id,
        session_id=session_id,
        symbol=order_in.symbol,
        side=order_in.side,
        quantity=order_in.quantity,
        reason=order_in.reason,
        timestamp=order_in.timestamp
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return LocalOrderResponse.from_orm(db_order)

@app.put("/orders/{order_id}/status", response_model=LocalOrderResponse)
def update_order_status(order_id: str, status_update: OrderStatusUpdate, db: Session = Depends(get_db)):
    print(f"[BotService] Updating Status: {order_id} -> {status_update.status}")
    db_order = db.query(LocalOrder).filter(LocalOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Local Order not found")
    
    db_order.status = status_update.status
    db.commit()
    db.refresh(db_order)
    return LocalOrderResponse.from_orm(db_order)

def match_fifo_orders(db: Session, sell_exec: GlobalExecution, bot_id: str):
    """
    봇별 격리(Isolated)를 지원하는 선입선출(FIFO) 매칭 엔진입니다.
    SELL 체결 건을 해당 봇의 미청산 BUY 건들과 매칭하여,
    BUY 건의 'remaining_qty'를 차감하고 SELL 건의 'realized_pnl'(실현 손익)을 계산합니다.
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
        
        # 매칭 수량 결정
        match_qty = min(buy_lot.remaining_qty, sell_qty_remain)
        
        # 해당 청크에 대한 총 손익(Gross PnL) 계산
        # (매도 단가 - 매수 단가) * 매칭 수량
        pnl_chunk = (sell_exec.price - buy_lot.price) * match_qty
        total_pnl += pnl_chunk
        
        # BUY Lot 상태 업데이트 (잔여 수량 차감)
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
        
    # Update Session PnL & Fee
    # Fee is always accumulated regardless of PnL
    if db_order.session_id:
        session = db.query(BotSession).filter(BotSession.id == db_order.session_id).first()
        if session:
            summary = session.get_summary()
            
            # Update Stats (PnL, WinRate, TradeCount)
            # PnL logic implies a closed trade (SELL side mostly)
            if db_exec.realized_pnl != 0:
                current_pnl = summary.get("total_pnl", 0.0)
                summary["total_pnl"] = current_pnl + db_exec.realized_pnl
                
                # Update Trade Count & Win Count
                current_trades = summary.get("trade_count", 0) + 1
                summary["trade_count"] = current_trades
                
                current_wins = summary.get("win_count", 0)
                if db_exec.realized_pnl > 0:
                    current_wins += 1
                    summary["win_count"] = current_wins
                
                # Recalculate Win Rate
                if current_trades > 0:
                    summary["win_rate"] = current_wins / current_trades
                else:
                    summary["win_rate"] = 0.0

            # Update Fee (Always)
            if db_exec.fee > 0:
                current_fee = summary.get("total_fee", 0.0)
                summary["total_fee"] = current_fee + db_exec.fee
            
            session.set_summary(summary)
            db.add(session)
            db.commit()
            print(f"[Session] Updated Session {session.id}: PnL={summary.get('total_pnl', 0):.4f}, WinRate={summary.get('win_rate', 0):.2f}, Fee={summary.get('total_fee', 0):.4f}")
    
    return {"ok": True, "realized_pnl": db_exec.realized_pnl}

@app.get("/bots/{bot_id}/stats", response_model=BotStatsResponse)
def get_bot_stats(bot_id: str, db: Session = Depends(get_db)):
    """
    특정 봇의 누적 통계를 계산합니다.
    통계는 SELL 체결 건들의 실현 손익(realized PnL)을 집계하여 도출됩니다.
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
        pnl = exc.realized_pnl or 0.0
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
        profit_factor = None if gross_profit > 0 else 0.0
    else:
        profit_factor = gross_profit / gross_loss

    return BotStatsResponse(
        total_pnl=total_pnl,
        win_rate=win_rate,
        total_trades=total_trades,
        profit_factor=profit_factor,
        average_pnl=average_pnl
    )
