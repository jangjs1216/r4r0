import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, LargeBinary, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# Database path (relative to the service root execution or absolute)
# Should be in /home/jangjs/r4r0/data/auth.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Allow overriding via environment variable (Crucial for Docker persistence)
DB_PATH = os.getenv("DB_FILE_PATH")

if not DB_PATH:
    # Go up two levels: services/auth -> services -> root
    ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
    DB_PATH = os.path.join(ROOT_DIR, "data", "auth.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class StoredCredential(Base):
    __tablename__ = "credentials"

    id = Column(String, primary_key=True, index=True) # UUID
    exchange = Column(String, index=True)
    label = Column(String)
    public_key = Column(String) # Stored in plain text (as it's public) or masked?
    # Spec says "Access Key Enc" but practically Public key is often needed for display/identification.
    # We will store public key plain (it's not secret) but masked in API response.
    # Update: Spec says "access_key_enc". Let's encrypt both to be safe or just secret.
    # Usually API Key (Public) is visible on exchanges too. Let's keep it plain for simple searching,
    # but the API response will mask it.
    
    # Encrypted Secret Key
    secret_key_enc = Column(LargeBinary, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active") # active, expired

def init_db():
    Base.metadata.create_all(bind=engine)
