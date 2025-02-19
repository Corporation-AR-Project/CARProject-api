# user.py
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from ..db.database import get_db
from starlette import status
from ..db.crud import users_crud
from ..db.schema import users_schema
from ..db.crud.users_crud import pwd_context
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from dotenv import load_dotenv
import os
from datetime import timedelta, datetime

# env 파일 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]

router = APIRouter(
    prefix="/user"
)

# 회원가입
@router.post("/join", status_code=status.HTTP_204_NO_CONTENT)
def join_user(_users_create: users_schema.UsersCreate, db : Session = Depends(get_db)) :
    # user 존재하는지 체크
    user = users_crud.get_existing_user(db, user_create=_users_create)
    if user : # 있으면 에러
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 존재하는 사용자입니다.")
    # 없으면 생성
    users_crud.create_user(db = db, user_create=_users_create)

# 로그인
@router.post("/login", response_model=users_schema.LoginToken)
def login_user(response: Response, form_data : OAuth2PasswordRequestForm = Depends(), db : Session = Depends(get_db)) :
    # login check
    user = users_crud.get_user(db, form_data.username)
    if not user or not pwd_context.verify(form_data.password, user.password) : 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 혹은 비밀번호가 틀렸습니다.",
            headers={"WWW-Authenticate" : "Bearer"}
        )
    # make access token
    data = {
        "sub" : user.userid,
        "exp" : datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    access_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    
    # 쿠키 저장
    response.set_cookie(key="access_token", value=access_token, expires=data['exp'], httponly=True)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username
    }

# 로그아웃
@router.get("/logout")
def logout_user(response : Response, request : Request) :
    access_token = request.cookies.get("access_token")

    # 쿠키 삭제
    response.delete_cookie(key="access_token")
    return HTTPException(status_code=status.HTTP_200_OK, detail = "로그아웃에 성공했습니다.")
