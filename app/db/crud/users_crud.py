from ..models import Users
from ..schema.users_schema import UsersCreate
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# 비밀번호 암호화(bcrypt 사용)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 회원 생성
def create_user(db : Session, user_create : UsersCreate) : 
    db_user = Users(userid = user_create.userid, # 아이디
                    username = user_create.username, # 비밀번호
                    useremail = user_create.useremail, # 이메일
                    password = pwd_context.hash(user_create.password), # 비밀번호, pwd_context 사용해서 암호화
                    birthday = user_create.birthday, # 생일
                    gender = user_create.gender, # 성별
                    foreginer = user_create.foreginer) # 외국인 여부
    db.add(db_user) # db에 생성
    db.commit() # DB에 commit

# 유저 있는지 확인
def get_existing_user(db : Session, user_create : UsersCreate) :
    return db.query(Users).filter(
        (Users.userid == user_create.userid) # 유저 아이기가 같은 사람 찾기
    ).first() # 제일 처음 한명만 가져옴

# 유저 검색
def get_user(db : Session, userid : str) : 
    return db.query(Users).filter(Users.userid == userid).first() # 아이디와 같은 사람 찾기
