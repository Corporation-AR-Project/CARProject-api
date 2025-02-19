from ..models import Users
from ..schema.users_schema import UsersCreate
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# 비밀번호 암호화
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(db : Session, user_create : UsersCreate) : 
    db_user = Users(username = user_create.username,
                    useremail = user_create.useremail,
                    password = pwd_context.hash(user_create.password))
    db.add(db_user)
    db.commit()

def get_existing_user(db : Session, user_create : UsersCreate) :
    return db.query(Users).filter(
        (Users.username == user_create.username) | 
        (Users.useremail == user_create.useremail)
    ).first()

def get_user(db : Session, username : str) : 
    return db.query(Users).filter(Users.username == username).first()
