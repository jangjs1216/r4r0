import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Append parent directory to sys.path to import main
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from main import app, get_db
from models import Base, BotSession, LocalOrder

# Setup Test DB (In-Memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def init_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_session_lifecycle():
    # 1. Create Bot
    bot_res = client.post("/bots", json={"name": "TestBot"})
    assert bot_res.status_code == 200
    bot_id = bot_res.json()["id"]

    # 2. Start Bot (Create Session)
    start_res = client.post(f"/bots/{bot_id}/start")
    assert start_res.status_code == 200
    session_data = start_res.json()
    assert session_data["status"] == "ACTIVE"
    assert session_data["end_time"] is None
    session_id = session_data["id"]

    # 3. Create Order (Auto-link)
    order_res = client.post("/orders", json={
        "bot_id": bot_id,
        "symbol": "BTC/USDT",
        "side": "BUY",
        "quantity": 1.0,
        "reason": "Test"
    })
    assert order_res.status_code == 200
    order_data = order_res.json()
    assert order_data["session_id"] == session_id

    # 4. Stop Bot (Close Session)
    stop_res = client.post(f"/bots/{bot_id}/stop")
    assert stop_res.status_code == 200
    closed_session = stop_res.json()
    assert closed_session["id"] == session_id
    assert closed_session["status"] == "ENDED"
    assert closed_session["end_time"] is not None

def test_pnl_aggregation():
    # 1. Setup Bot & Session
    bot_res = client.post("/bots", json={"name": "PnLBot"})
    bot_id = bot_res.json()["id"]
    client.post(f"/bots/{bot_id}/start")
    
    # 2. Create Order
    order_res = client.post("/orders", json={
        "bot_id": bot_id,
        "symbol": "ETH/USDT",
        "side": "SELL",
        "quantity": 0.5
    })
    local_order_id = order_res.json()["id"]

    # 3. Record Execution (With PnL)
    # Note: match_fifo_orders logic is mocked or we assume simple update
    # In main.py, we directly update session summary if realized_pnl != 0.
    # We don't check FIFO matching logic here (as it depends on BUY orders), 
    # but we pass realized_pnl in execution request? 
    # Wait, execution request doesn't have realized_pnl as input. 
    # It calculates it. 
    # To test calculation, we need a BUY order first.
    
    # 3.1 BUY Order
    buy_order = client.post("/orders", json={"bot_id": bot_id, "symbol": "ETH/USDT", "side": "BUY", "quantity": 1.0}).json()
    client.post("/executions", json={
        "local_order_id": buy_order["id"],
        "symbol": "ETH/USDT", "side": "BUY", "price": 1000.0, "quantity": 1.0, "quote_qty": 1000.0,
        "exchange_trade_id": "t1", "exchange_order_id": "o1", "order_list_id": "l1", "fee": 0, "fee_asset": "USDT",
        "timestamp": "2024-01-01T10:00:00"
    })

    # 3.2 SELL Order (Trigger PnL)
    sell_res = client.post("/executions", json={
        "local_order_id": local_order_id,
        "symbol": "ETH/USDT", "side": "SELL", "price": 1100.0, "quantity": 0.5, "quote_qty": 550.0,
        "exchange_trade_id": "t2", "exchange_order_id": "o2", "order_list_id": "l2", "fee": 0, "fee_asset": "USDT",
        "timestamp": "2024-01-01T10:05:00"
    })
    assert sell_res.json()["realized_pnl"] == 50.0
    # PnL should be (1100 - 1000) * 0.5 = 50.0

    # 4. Check Session Summary & Orders (Detail View)
    sessions = client.get(f"/bots/{bot_id}/sessions").json()
    assert len(sessions) > 0
    active_session_summary = sessions[0]["summary"]
    
    # Detail View Check
    s_detail = client.get(f"/sessions/{sessions[0]['id']}").json()
    assert "orders" in s_detail
    assert len(s_detail["orders"]) >= 2
    
    assert active_session_summary.get("total_pnl") == 50.0
