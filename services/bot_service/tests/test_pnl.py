import sys
from datetime import datetime
import uuid

# Import BotService components
# Ensure we can import from local directory
import models
from models import Bot, LocalOrder, GlobalExecution, SessionLocal, engine, Base
from main import match_fifo_orders

def setup_db():
    # Use in-memory DB or temporary file for testing
    models.DATABASE_URL = "sqlite:///:memory:" 
    # Re-bind engine (hacky for test script but works if models.py uses global engine)
    # Actually models.py creates engine on import. We will use the existing engine but dropping all tables first to clear state
    # or just use the existing bots.db if we want persistence.
    # Ideally use test db. For now, let's just insert test data into existing DB and clean up, or assume specific IDs.
    pass

def test_pnl_logic():
    print("=== Starting PnL Logic Test ===")
    session = SessionLocal()
    
    try:
        # 1. Create Test Bot
        bot_id = str(uuid.uuid4())
        print(f"Creating Bot: {bot_id}")
        bot = Bot(id=bot_id, name="TestBot_PnL", status="RUNNING")
        session.add(bot)
        session.commit()

        # 2. BUY 1: 1 BTC @ 100 USDT
        print("--- Executing BUY 1: 1 BTC @ 100 ---")
        lo1 = LocalOrder(id=str(uuid.uuid4()), bot_id=bot_id, symbol="BTC/USDT", side="BUY", quantity=1.0)
        session.add(lo1)
        session.commit()

        exec1 = GlobalExecution(
            id=f"trade_{uuid.uuid4()}",
            local_order_id=lo1.id,
            exchange_order_id="ord1",
            symbol="BTC/USDT",
            side="BUY",
            price=100.0,
            quantity=1.0,
            quote_qty=100.0,
            timestamp=datetime.utcnow(),
            remaining_qty=1.0, # BUY logic sets this
            realized_pnl=0.0
        )
        session.add(exec1)
        session.commit()

        # 3. BUY 2: 1 BTC @ 200 USDT
        print("--- Executing BUY 2: 1 BTC @ 200 ---")
        lo2 = LocalOrder(id=str(uuid.uuid4()), bot_id=bot_id, symbol="BTC/USDT", side="BUY", quantity=1.0)
        session.add(lo2)
        session.commit()

        exec2 = GlobalExecution(
            id=f"trade_{uuid.uuid4()}",
            local_order_id=lo2.id,
            exchange_order_id="ord2",
            symbol="BTC/USDT",
            side="BUY",
            price=200.0,
            quantity=1.0,
            quote_qty=200.0,
            timestamp=datetime.utcnow(),
            remaining_qty=1.0, 
            realized_pnl=0.0
        )
        session.add(exec2)
        session.commit()

        # 4. SELL: 1.5 BTC @ 300 USDT (Should match 1.0 from BUY1 + 0.5 from BUY2)
        print("--- Executing SELL: 1.5 BTC @ 300 ---")
        lo3 = LocalOrder(id=str(uuid.uuid4()), bot_id=bot_id, symbol="BTC/USDT", side="SELL", quantity=1.5)
        session.add(lo3)
        session.commit()

        exec_sell = GlobalExecution(
            id=f"trade_{uuid.uuid4()}",
            local_order_id=lo3.id,
            exchange_order_id="ord3",
            symbol="BTC/USDT",
            side="SELL",
            price=300.0,
            quantity=1.5,
            quote_qty=450.0,
            timestamp=datetime.utcnow(),
            remaining_qty=0.0,
            realized_pnl=0.0
        )
        session.add(exec_sell) # Add first to session
        
        # RUN FIFO ENGINE
        match_fifo_orders(session, exec_sell, bot_id)
        session.commit()

        # 5. Verification
        print("\n=== Verification Results ===")
        session.refresh(exec1)
        session.refresh(exec2)
        session.refresh(exec_sell)

        print(f"BUY 1 Remaining Qty: {exec1.remaining_qty} (Expected: 0.0)")
        print(f"BUY 2 Remaining Qty: {exec2.remaining_qty} (Expected: 0.5)")
        print(f"SELL Realized PnL: {exec_sell.realized_pnl} (Expected: (300-100)*1 + (300-200)*0.5 = 200 + 50 = 250.0)")

        assert exec1.remaining_qty == 0.0, "BUY 1 should be fully consumed"
        assert exec2.remaining_qty == 0.5, "BUY 2 should be partially consumed"
        assert exec_sell.realized_pnl == 250.0, "PnL Calculation Wrong"

        print("✅ PnL FIFO Logic Verified Successfully!")
        
        # Isolation Test
        print("\n--- Isolation Test ---")
        other_bot_id = str(uuid.uuid4())
        lo_other = LocalOrder(id=str(uuid.uuid4()), bot_id=other_bot_id, symbol="BTC/USDT", side="BUY", quantity=1.0)
        session.add(lo_other)
        exec_other = GlobalExecution(
            id=f"trade_{uuid.uuid4()}", local_order_id=lo_other.id, exchange_order_id="ord_other",
            symbol="BTC/USDT", side="BUY", price=100.0, quantity=1.0, timestamp=datetime.utcnow(), remaining_qty=1.0
        )
        session.add(exec_other)
        session.commit()
        
        # Sell from First Bot again
        lo4 = LocalOrder(id=str(uuid.uuid4()), bot_id=bot_id, symbol="BTC/USDT", side="SELL", quantity=1.0)
        session.add(lo4)
        exec_sell2 = GlobalExecution(
            id=f"trade_{uuid.uuid4()}", local_order_id=lo4.id, exchange_order_id="ord4",
            symbol="BTC/USDT", side="SELL", price=300.0, quantity=1.0, timestamp=datetime.utcnow()
        )
        match_fifo_orders(session, exec_sell2, bot_id)
        
        session.refresh(exec_other)
        print(f"Other Bot Remaining Qty: {exec_other.remaining_qty} (Expected: 1.0)")
        assert exec_other.remaining_qty == 1.0, "Isolation Failed! Consumed other bot's lot"
        print("✅ Isolation Verified!")

    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_pnl_logic()
