
import os
import sqlite3
import sys

# DB 경로 설정 (docker-compose 볼륨 마운트 경로에 맞춤)
DB_PATH = os.getenv("DATABASE_URL", "/app/bots.db").replace("sqlite:///", "")

def migrate_db():
    print(f"Checking database at {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print("Database not found. Skipping migration (will be created by app).")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 컬럼 존재 여부 확인
        cursor.execute("PRAGMA table_info(bots)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "status_message" not in columns:
            print("Migrating: Adding 'status_message' column to 'bots' table...")
            cursor.execute("ALTER TABLE bots ADD COLUMN status_message TEXT DEFAULT NULL")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column 'status_message' already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
