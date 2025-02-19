from pydantic import BaseModel, field_validator, EmailStr
from pydantic_core.core_schema import FieldValidationInfo
from datetime import date

class UsersCreate(BaseModel) : 
    userid : str
    username : str
    useremail : EmailStr
    password : str
    passwordCheck : str
    birthday : date
    gender : str
    foreginer : bool

    @field_validator('userid', 'username', 'useremail', 'password', 'passwordCheck')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('빈 값은 허용되지 않습니다.')
        return v
    
    @field_validator('passwordCheck')
    def password_match(cls, v, info : FieldValidationInfo) :
        if 'password' in info.data and v != info.data['password'] : 
            raise ValueError("비밀번호와 비밀번호 확인이 일치하지 않습니다.")
        return v

class LoginToken(BaseModel) : 
    access_token : str
    token_type : str
    username : str

