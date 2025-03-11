# user.py
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from ..db.database import get_db
from starlette import status
from ..db.crud import users_crud, company_crud
from ..db.schema import users_schema, company_schema
from ..db.crud.users_crud import pwd_context
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from dotenv import load_dotenv
import os
from datetime import timedelta, datetime

# env 파일 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"]) # access_token 종료 기간
SECRET_KEY = os.environ["SECRET_KEY"] # secret_key
ALGORITHM = os.environ["ALGORITHM"] # algorithm

# router 설정
router = APIRouter(
    prefix="/user"
)

# 회원가입 API (POST)
# API URL : http://localhost:8000/user/join
# 파라미터
# userid | str not null
# username | str not null
# useremail | str not null
# password | str not null
# passwordCheck | str not null
# birthday | date not null
# gender | str not null
# foreginer | boolean not null
# phone | str not null
@router.post("/join", status_code=status.HTTP_204_NO_CONTENT)
def join_user(_users_create: users_schema.UsersCreate, db : Session = Depends(get_db)) :
    # user 존재하는지 체크
    user = users_crud.get_existing_user(db, user_create=_users_create)
    if user : # 있으면 에러
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 존재하는 사용자입니다.")
    # 없으면 생성
    users_crud.create_user(db = db, user_create=_users_create)

# 로그인 API (POST)
# API URL : http://localhost:8000/user/login
# 파라미터
# username | str not null
# password | str not null
@router.post("/login", response_model=users_schema.LoginToken)
def login_user(response: Response, form_data : OAuth2PasswordRequestForm = Depends(), db : Session = Depends(get_db)) :
    # login 확인
    user = users_crud.get_user(db, userid = form_data.username)
    # 해당 userid의 유저가 없거나 비번이 틀린 경우
    if not user or not pwd_context.verify(form_data.password, user.password) : 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 혹은 비밀번호가 틀렸습니다.",
            headers={"WWW-Authenticate" : "Bearer"}
        )

    # 제한시간 등 정보 생성
    data = {
        "sub" : "login_token",
        "id" : user.id,
        "userid" : user.userid,
        "iat" : datetime.utcnow(),
        "exp" : datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    # access token 생성
    access_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    # 쿠키에 저장
    response.set_cookie(key="access_token", value=access_token, expires=ACCESS_TOKEN_EXPIRE_MINUTES, httponly=True)
    # 결과값 반환
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id" : user.id,
        "userid": user.userid
    }

# 로그아웃 API (GET)
# API URL : http://localhost:8000/user/logout
@router.get("/logout")
def logout_user(response : Response) :
    # 쿠키 삭제
    response.delete_cookie(key="access_token")
    return HTTPException(status_code=status.HTTP_200_OK, detail = "로그아웃에 성공했습니다.")

# 로그인 체크 API (GET)
# API URL : http://localhost:8000/user/auth
@router.get("/auth")
def isLogin_check(request : Request) :
    is_login = False
    access_token = request.cookies.get("access_token")
    if not access_token == None :
        is_login = True
        
    return { "is_login" : is_login }

# 회원 정보 조회 API (GET)
# API URL : http://localhost:8000/user/info
@router.get("/info")
def info_user(request : Request, db : Session = Depends(get_db)) : 
    access_token = request.cookies.get("access_token")
    if not jwt_token_check(access_token) :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="접근 권한이 없습니다.")
    else :
        info = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
        user = users_crud.get_user(db, userid = dict(info)['userid'])
        data = {
            'id' : user.id,
            'userid' : user.userid,
            'username' : user.username,
            'useremail' : user.useremail,
            'birthday' : user.birthday,
            'gender' : user.gender,
            'foreginer' : user.foreginer,
            'phone' : user.phone,
            'created_at' : user.created_at
        }
    return data

# 회원정보 업데이트 API (POST)
# API URL : http://localhost:8000/user/modify
# 파라미터
# username | str not null
# useremail | str not null
# birthday | date not null
# gender | str not null
# foreginer | boolean not null
# phone | str not null
@router.post("/modify", status_code=status.HTTP_204_NO_CONTENT)
def modify_user(_user_update : users_schema.UserInfoUpdate, request : Request, response : Response, db : Session = Depends(get_db)) :
    access_token = request.cookies.get("access_token")
    if not jwt_token_check(access_token, id = _user_update.id) :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="접근 권한이 없습니다.")
    else : 
        users_crud.update_user(db, user_update=_user_update)
        user = users_crud.get_user_id(db, id = _user_update.id)
        # 제한시간 등 정보 생성
        data = {
            "sub" : "login_token",
            "id" : user.id,
            "userid" : user.userid,
            "iat" : datetime.utcnow(),
            "exp" : datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        # access token 생성
        access_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        # 쿠키에 저장
        response.set_cookie(key="access_token", value=access_token, expires=ACCESS_TOKEN_EXPIRE_MINUTES, httponly=True)

# 비밀번호 수정 API (POST)
# API URL : http://localhost:8000/user/modify_password
# 파라미터
# password | str not null
# changePassword | str not null
@router.post("/modify_password", status_code=status.HTTP_204_NO_CONTENT)
def modify_password_user(_user_password_update : users_schema.UserPasswordUpdate, request : Request, db : Session = Depends(get_db)) :
    access_token = request.cookies.get("access_token")

    # login 확인
    user = users_crud.get_user_id(db, id = _user_password_update.id)
    # 해당 userid의 유저가 없거나 비번이 틀린 경우
    if not user or not pwd_context.verify(_user_password_update.password, user.password) : 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="기존 비밀번호가 일치하지 않습니다.",
            headers={"WWW-Authenticate" : "Bearer"}
        )

    if not jwt_token_check(access_token, id = _user_password_update.id) : 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="접근 권한이 없습니다.")
    else :
        users_crud.update_password_user(db, user_password_update=_user_password_update)

# 회원 탈퇴 API (POST)
# API URL : http://localhost:8000/user/withdraw
# 파라미터
# id | int not null
@router.post("/withdraw", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_user(id : int, request : Request, response : Response, db : Session = Depends(get_db)) :
    access_token = request.cookies.get("access_token")
    if not jwt_token_check(access_token, id) : 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="접근 권한이 없습니다.")
    else :
        users_crud.withdraw_user(db, id)
        response.delete_cookie(key="access_token")

# jwt token 체크
def jwt_token_check(access_token, id = None) : 
    flag = False
    if not access_token == None : 
        info = dict(jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM))
        if id == None or id == info['id'] : 
            flag = True
    return flag

# 아이디 중복 확인 API (GET)
# API URL : http://localhost:8000/user/duplicationCheck
# 파라미터
# userid | str not null
@router.get("/duplicationCheck")
def userid_duplicateCheck(userid : str, db : Session = Depends(get_db)) :
    user = users_crud.get_user(db, userid)
    result = { "is_duplication" : True }
    if user == None :
        result = { "is_duplication" : False }

    return result

# 관심 기업 목록 검색 API (GET)
# API URL : http://localhost:8000/user/interest_company_list
# 파라미터
# page | int not null default = 1
# limit | int not null default = 10
@router.get("/interest_company_list")
def search_interest_company_list(request : Request, page : int = 1, limit : int = 10, db : Session = Depends(get_db)) :
    access_token = request.cookies.get("access_token")
    if not jwt_token_check(access_token) :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="접근 권한이 없습니다.")
    else :
        info = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
        user = users_crud.get_user(db, userid = dict(info)['userid'])
        start = (page - 1)  * limit
        total, _interest_list = company_crud.search_interest_list(db, user_id=user.id, page = start, limit = limit)
        interest_list = []
        for item in _interest_list :
            interest_list.append({
                "id" : item[0].id,
                "company_name" : item[1].name,
                "company_id" : item[0].company_id,
                "user_id" : item[0].user_id,
                "created_at" : item[0].created_at
            })

        return {
            "total" : total,
            "list" : interest_list
        }

# 관심 기업 등록 API (POST)
# API URL : http://localhost:8000/user/add_interest_company
# 파라미터
# company_id | int not null
@router.post("/add_interest_company", status_code=status.HTTP_202_ACCEPTED)
def create_interest_company(request : Request, company_id : int, db : Session = Depends(get_db)) :
    access_token = request.cookies.get("access_token")
    if not jwt_token_check(access_token) :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="접근 권한이 없습니다.")
    else :
        info = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
        user = users_crud.get_user(db, userid = dict(info)['userid'])
        company_crud.create_interest_company(db, company_schema.InterestCompanyCreate(user_id = user.id, company_id=company_id))
        return { "msg" : "성공적으로 관심 기업이 등록되었습니다." }

# 관심 기업 해제 API (POST)
# API URL : http://localhost:8000/user/remove_interest_company
# 파라미터
# interest_id | int not null
@router.post("/remove_interest_company")
def delete_interest_company(request : Request, interest_id : int, db : Session = Depends(get_db)) :
    access_token = request.cookies.get("access_token")
    if not jwt_token_check(access_token) :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="접근 권한이 없습니다.")
    else :
        company_crud.delete_interest_company(db, interest_id)
        return { "msg" : "성공적으로 관심 기업이 해제되었습니다." }

# 검색 목록 조회 API (GET)
# API URL : http://localhost:8000/user/search_history_list
# 파라미터
# page | int not null default = 1
# limit | int not null default = 10
@router.get("/search_history_list")
def search_history_list(request : Request, page : int = 1, limit : int = 10, db : Session = Depends(get_db)) : 
    access_token = request.cookies.get("access_token")
    if not jwt_token_check(access_token) :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="접근 권한이 없습니다.")
    else :
        info = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
        user = users_crud.get_user(db, userid = dict(info)['userid'])
        start = (page - 1)  * limit
        total, _history_list = company_crud.search_history_list(db, user_id=user.id, page=start, limit = limit)
        history_list = []
        for item in _history_list : 
            data = item.__dict__
            history_list.append({
                "id" : data['id'],
                "user_id" : data['user_id'],
                "company_id" : data['company_id'],
                "company_name" : data['company_name'],
                "start_year" : data['start_year'],
                "end_year" : data['end_year'],
                "created_at" : data['created_at']
            })
        return {
            "total" : total,
            "history_list" : history_list
        }

# 검색 기록 삭제 API (POSt)
# API URL : http://localhost:8000/user/remove_search_history
# 파라미터
# history_id | int not null
@router.post("/remove_search_history")
def remove_search_history(request : Request, history_id : int, db : Session = Depends(get_db)) : 
    access_token = request.cookies.get("access_token")
    if not jwt_token_check(access_token) :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="접근 권한이 없습니다.")
    else :
        company_crud.delete_search_history(db, history_id)
        return { "msg" : "해당 검색 기록이 정상적으로 삭제되었습니다." }

# 아이디 찾기 API
@router.post("/find_userid")
def find_userid(_find_userid : users_schema.FindUserid, db : Session = Depends(get_db)) : 
    user = users_crud.find_userid(db, _find_userid = _find_userid)
    result = { "msg" : "해당하는 유저 정보가 없습니다." }
    if not user == None : 
        result = { "userid" : user.userid }
    
    return result

# 비밀번호 찾기 API
@router.post("/find_password")
def find_userpw(_find_password : users_schema.FindPassword, db : Session = Depends(get_db)) :
    new_password = users_crud.find_password(db, _find_password)
    result = { "msg" : "해당하는 유저 정보가 없습니다." }
    if new_password != "" : 
        result = { "new_password" : new_password }
    
    return result