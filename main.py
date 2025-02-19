# main.py
# uvicorn main:app --reload

from fastapi import FastAPI # FastAPI import
from starlette.middleware.cors import CORSMiddleware

from app.router import company, user

app = FastAPI()

# cors 예외
origins = [
    "http://127.0.0.1:8000",
    "http://localhost",
    "http://localhost:8000",
]

# app middleware 처리
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 API
@app.get("/")
def default() : 
    return {
        "status": "success",
        "data": {}
    }

# /~ router 추가
app.include_router(company.router, tags=['company'])
app.include_router(user.router, tags=['user'])