# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

## alembic 초기화 작업
## alembic revision --autogenerate
## alembic upgrade head

# SQLite DB 생성
# 최상위 폴더에 myapi.db 생성
SQLALCHEMY_DATABASE_URL = "sqlite:///./myapi.db"

# engine 설정
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# base 생성
Base = declarative_base()

# db 연결
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
