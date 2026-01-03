import sys
import os
import uuid
from datetime import datetime, timedelta
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path to allow importing models
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from sqlalchemy import text
from models import SessionLocal, BotSession, LocalOrder, engine, Base, Bot

def migrate_sessions():
    """
    1. Create 'bot_sessions' table if not exists.
    2. Backfill sessions for orphaned orders (cluster by 1 hour gap).
    """
    logger.info("Starting Session Migration...")

    # 1. Create Tables
    # This will create bot_sessions if it doesn't exist.
    # It also handles column additions if using Alembic, but here we rely on create_all for new tables.
    # Note: create_all does NOT update existing tables (e.g. adding columns). 
    # For LocalOrder.session_id, if the column is missing in DB but present in Model, 
    # SQLAlchemy create_all won't add it to an existing table. 
    # We might need a raw SQL alter for SQLite if not using Alembic.
    
    logger.info("Ensuring schema...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if LocalOrder table has session_id column
        # SQLite specific check
        result = db.execute(text("PRAGMA table_info(local_orders)")).fetchall()
        columns = [row[1] for row in result]
        if 'session_id' not in columns:
            logger.info("Adding session_id column to local_orders...")
            db.execute(text("ALTER TABLE local_orders ADD COLUMN session_id VARCHAR"))
            db.commit()
        
        # 2. Fetch Orphaned Orders
        orphans = db.query(LocalOrder).filter(LocalOrder.session_id == None).order_by(LocalOrder.bot_id, LocalOrder.timestamp).all()
        
        if not orphans:
            logger.info("No orphaned orders found. Migration complete.")
            return

        logger.info(f"Found {len(orphans)} orphaned orders. Clustering into sessions...")
        
        # Group by Bot
        orders_by_bot = {}
        for o in orphans:
            if o.bot_id not in orders_by_bot:
                orders_by_bot[o.bot_id] = []
            orders_by_bot[o.bot_id].append(o)
            
        TIME_GAP_THRESHOLD = timedelta(hours=1)
        created_sessions = 0
        
        for bot_id, orders in orders_by_bot.items():
            if not orders: continue
            
            # Clustering Algorithm
            current_session = None
            last_order_time = None
            
            for order in orders:
                is_new_session = False
                
                if current_session is None:
                    is_new_session = True
                elif order.timestamp - last_order_time > TIME_GAP_THRESHOLD:
                    # Gap detected, close previous session and start new one
                    current_session.end_time = last_order_time + timedelta(minutes=5) # Padding
                    current_session.status = "ENDED"
                    is_new_session = True
                
                if is_new_session:
                    # Create new session
                    session_id = str(uuid.uuid4())
                    current_session = BotSession(
                        id=session_id,
                        bot_id=bot_id,
                        start_time=order.timestamp - timedelta(seconds=1), # Slightly before first order
                        status="ACTIVE", # Will be closed if gap found or at end of loop if old
                        summary_json="{}"
                    )
                    db.add(current_session)
                    created_sessions += 1
                    # Flush to get ID if needed, but we set it manually
                
                # Link Order
                order.session_id = current_session.id
                last_order_time = order.timestamp
            
            # Close the last session for this bot
            if current_session:
                current_session.end_time = last_order_time + timedelta(minutes=5)
                current_session.status = "ENDED"
        
        db.commit()
        logger.info(f"Migration Successful. Created {created_sessions} sessions for backfilled orders.")
        
    except Exception as e:
        logger.error(f"Migration Failed: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    migrate_sessions()
