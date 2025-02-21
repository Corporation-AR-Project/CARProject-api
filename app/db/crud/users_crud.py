from ..models import Users
from ..schema.users_schema import UsersCreate, UserInfoUpdate, UserPasswordUpdate
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import update, delete

# 비밀번호 암호화(bcrypt 사용)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 회원 생성
def create_user(db : Session, user_create : UsersCreate) : 
    db_user = Users(userid = user_create.userid, # 아이디
                    username = user_create.username, # 이름
                    useremail = user_create.useremail, # 이메일
                    password = pwd_context.hash(user_create.password), # 비밀번호, pwd_context 사용해서 암호화
                    birthday = user_create.birthday, # 생일
                    gender = user_create.gender, # 성별
                    foreginer = user_create.foreginer, # 외국인 여부
                    phone = user_create.phone # 전화번호
                    )
    db.add(db_user) # db에 생성
    db.commit() # DB에 commit

# 유저 있는지 확인
def get_existing_user(db : Session, user_create : UsersCreate) :
    return db.query(Users).filter(
        (Users.userid == user_create.userid) # 유저 아이디가 같은 사람 찾기
    ).first() # 제일 처음 한명만 가져옴

# 유저 검색
def get_user(db : Session, userid : str) : 
    return db.query(Users).filter(Users.userid == userid).first() # 아이디와 같은 사람 찾기

# 유저 검색(id)
def get_user_id(db : Session, id : int) : 
    return db.query(Users).filter(Users.id == id).first() # 아이디와 같은 사람 찾기

# 회원 수정
def update_user(db : Session, user_update : UserInfoUpdate) :
    stmt = (
        update(Users)
        .where(
            Users.id == user_update.id, # 아이디
        )
        .values(
            username = user_update.username, # 이름
            useremail = user_update.useremail, # 이메일
            birthday = user_update.birthday, # 생일
            gender = user_update.gender, # 성별
            foreginer = user_update.foreginer, # 내외국인
            phone = user_update.phone # 전화번호
        )
    )
    db.execute(stmt) # db에 넣고
    db.commit() # 커밋

# 비밀번호 수정
def update_password_user(db : Session, user_password_update : UserPasswordUpdate) :
    stmt = (
        update(Users)
        .where(
            Users.id == user_password_update.id
        )
        .values(
            password = pwd_context.hash(user_password_update.changePassword)
        )
    )
    db.execute(stmt)
    db.commit()

# 회원 탈퇴
def withdraw_user(db : Session, id : int) : 
    stmt = (
        delete(Users)
        .where(
            Users.id == id
        )
    )
    db.execute(stmt)
    db.commit()
