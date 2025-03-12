from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, Boolean
from datetime import datetime
from .database import Base
from sqlalchemy.orm import relationship

# 회사 테이블
class Company(Base) : 
    __tablename__ = "company" # 테이블 명 : company

    id = Column(Integer, primary_key=True, autoincrement=True) # id(아이디) | integer, primary key, autoincrement
    name = Column(String, nullable=False) # name(회사명) | string, not null
    jongmok_code = Column(String, nullable=True) # jongmok_code(종목코드) | string, null
    industry_code = Column(String, nullable=True) # industry_code(업종코드) | string, null
    industry_name = Column(String, nullable=True) # industry_name(업종명) | string, null
    is_visible = Column(Boolean, nullable=False, default=True) # is_visible(노출여부) | boolean, not null, default = True

# 회사 년도별 정보 테이블
class CompanyYearInfo(Base) :
    __tablename__ = "company_year_info" # 테이블명 : company_year_info

    id = Column(Integer, primary_key=True, autoincrement=True) # id(아이디) | integer, primary key, autoincrement
    company_id = Column(Integer, ForeignKey("company.id")) # company_id(회사 테이블 아이디) | integer, foreignKey(Company Table - id)
    year = Column(String, nullable=False) # year(년도) | String, not null
    current_assets = Column(Integer, nullable=True) # current_assets(유동자산) | integer, null
    total_assets = Column(Integer, nullable=True) # total_asset(자산총계) | integer, null
    current_liabilities = Column(Integer, nullable=True) # current_liabilities(유동부채) | integer, null
    total_debt = Column(Integer, nullable=True) # total_debt(부채총계) | integer, null
    total_capital = Column(Integer, nullable=True) # total_capital(자본총계) | integer, null
    revenue = Column(Integer, nullable=True) # revenue(매출액) | integer, null
    cost_revenue = Column(Integer, nullable=True) # cost_revenue(매출원가) | integer, null
    total_revenue = Column(Integer, nullable=True) # total_revenue(매출총이익) | integer, null
    expenses = Column(Integer, nullable=True) # expenses(판매비와관리비) | integer, null
    operating_profit = Column(Integer, nullable=True) # operating_profit(영업이익) | integer, null
    net_profit = Column(Integer, nullable=True) # net_profit(순이익) | integer, null
    is_visible = Column(Boolean, nullable=False, default=True) # is_visible(노출여부) | boolean, not null, default = True

# 관심 기업 테이블
class InteresetCompany(Base) : 
    __tablename__ = "interest_company" # 테이블명 : interest_company

    id = Column(Integer, primary_key=True, autoincrement=True) # id(아이디) | integer, primary key, autoincrement
    user_id = Column(Integer, ForeignKey("users.id")) # user_id(유저 테이블 아이디) | integer, foreignKey(Users Table - id)
    company_id = Column(Integer, ForeignKey("company.id")) # company_id(회사 테이블 아이디) | integer, foreginKey(Company Table - id)
    created_at = Column(DateTime, nullable=False, default=datetime.now) # created_at(생성일자) | datetime, not null, default = datetime.now

# 유저 테이블
class Users(Base) :
    __tablename__ = "users" # 테이블명 : users

    id = Column(Integer, primary_key=True, autoincrement=True) # id(아이디) | integer, primary key, autoincrement
    userid = Column(String, nullable=False) # userid(유저 아이디) | string, not null
    username = Column(String, nullable=False) # username(유저명) | string, not null
    useremail = Column(String, nullable=False) # useremail(이메일) | string, not null
    password = Column(String, nullable=False) # password(비밀번호) | string, not null
    birthday = Column(Date, nullable=True) # birthday(생일) | date, null
    gender = Column(String, nullable=True) # gender(성별) | string, null
    foreginer = Column(Boolean, nullable=True) # foreginer(외국인 여부) | boolean, null
    phone = Column(String, nullable=True) # phone(전화번호) | String, null
    created_at = Column(DateTime, nullable=False, default=datetime.now) # created_at(생성일자) | datetime, not null, default = datetime.now

# 검색 기록 테이블
class SearchHistory(Base) : 
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True) # id(아이디) | integer, primary key, autoincrement
    user_id = Column(Integer, ForeignKey("users.id")) # user_id(유저 테이블 아이디) | integer, foreginKey(Users Table - id)
    company_id = Column(Integer, ForeignKey("company.id")) # company_id(기업 테이블 아이디) | integer, foreginKey(Company Table - id)
    company_name = Column(String, nullable=False) # company_name(회사명) | String, not null
    start_year = Column(String, nullable=True) # start_year(검색 시작 년도) | String, null
    end_year = Column(String, nullable=True) # end_year(검색 끝 년도) | String, null
    created_at = Column(DateTime, nullable=False, default=datetime.now) # created_at(생성날짜) | datetime, not null, default = datetime.now

# 이름 변경 목록 테이블
class CompanyRename(Base) : 
    __tablename__ = "company_rename"

    id = Column(Integer, primary_key=True, autoincrement=True) # id(아이디) | integer, primary key, autoincrement
    company_id = Column(Integer, ForeignKey("company.id")) # company_id(기업 id) | integer, foreginKey(Company Table - id)
    old_name = Column(String, nullable=False) # old_name(이전 이름) | String, not null
    new_name = Column(String, nullable=False) # new_name(최신 이름) | String, not null
    created_at = Column(DateTime, nullable=False, default=datetime.now) # created_at(생성날짜) | datetime, not null, default = datetime.now

# 공공데이터 검색용 이름 테이블
class CompanyInfoRename(Base) : 
    __tablename__ = "company_info_rename"

    id = Column(Integer, primary_key=True, autoincrement=True) # id(아이디) | integer, primary key, autoincrement
    company_id = Column(Integer, ForeignKey("company.id")) # company_id(기업 id) | integer, foreginKey(Company Table - id)
    search_name = Column(String, nullable=False) # search_name(검색용 이름 = 법인명) | String null able
    crno = Column(String, nullable=True) # crno(법인등록번호) | string, null able
    created_at = Column(DateTime, nullable=False, default=datetime.now) # created_at(생성날짜) | datetime, not null, default = datetime.now
