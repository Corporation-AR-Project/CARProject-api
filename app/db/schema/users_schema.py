from pydantic import BaseModel, field_validator, EmailStr
from pydantic_core.core_schema import FieldValidationInfo
from datetime import date

# 회원 생성
class UsersCreate(BaseModel) : 
    userid : str # 아이디
    username : str # 이름
    useremail : EmailStr # 이메일
    password : str # 비밀번호
    passwordCheck : str # 비밀번호 확인
    birthday : date # 생일
    gender : str # M(남자) / F(여자)
    foreginer : bool # 외국인 여부 (0 : 내국인 / 1 : 외국인)
    phone : str # 전화번호

    # 입력값 체크
    @field_validator('userid', 'username', 'useremail', 'password', 'passwordCheck')
    def not_empty(cls, v):
        if not v or not v.strip(): # 빈값 있는지 확인
            raise ValueError('빈 값은 허용되지 않습니다.') # 경고메시지
        return v
    
    # 비밀번호 확인 체크
    @field_validator('passwordCheck')
    def password_match(cls, v, info : FieldValidationInfo) :
        if 'password' in info.data and v != info.data['password'] : 
            raise ValueError("비밀번호와 비밀번호 확인이 일치하지 않습니다.") # 경고 메시지
        return v

# 비밀번호 변경
class UserPasswordUpdate(BaseModel) :
    id : int # id
    password : str # 비밀번호
    changePassword : str # 바꿀 비밀번호

    # 입력값 체크
    @field_validator('password', 'changePassword')
    def not_empty(cls, v) : 
        if not v or not v.strip() : # 빈값 있는지 확인
            raise ValueError('빈 값은 허용되지 않습니다.') # 경고 메시지
        return v

# 회원정보 변경
class UserInfoUpdate(BaseModel) :
    id : int # id
    username : str # 이름
    useremail : EmailStr # 이메일
    birthday : date # 생일
    gender : str # M(남자) / F(여자)
    foreginer : bool # 외국인 여부 (0 : 내국인 / 1 : 외국인)
    phone : str # 휴대폰

# 로그인 토큰
class LoginToken(BaseModel) : 
    access_token : str # access JWT 토큰
    token_type : str # 토큰 유형
    id : int # idx
    userid : str # 유저 아이디

