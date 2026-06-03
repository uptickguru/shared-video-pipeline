from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from models import Base

# Setup SQLAlchemy engine and session
engine = create_engine(
    settings.db_url, connect_args={"check_same_thread": False} # check_same_thread needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
