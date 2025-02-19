from ..models import Users
from ..schema.users_schema import UsersCreate
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# 비밀번호 암호화
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(db : Session, user_create : UsersCreate) : 
    db_user = Users(userid = user_create.userid,
                    username = user_create.username,
                    useremail = user_create.useremail,
                    password = pwd_context.hash(user_create.password),
                    birthday = user_create.birthday,
                    gender = user_create.gender,
                    foreginer = user_create.foreginer)
    db.add(db_user)
    db.commit()

def get_existing_user(db : Session, user_create : UsersCreate) :
    return db.query(Users).filter(
        (Users.userid == user_create.userid)
    ).first()

def get_user(db : Session, username : str) : 
    return db.query(Users).filter(Users.userid == username).first()
