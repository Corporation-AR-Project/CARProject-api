from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from .database import Base

class Company(Base) : 
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    industry_code = Column(String, nullable=True)
    industry_name = Column(String, nullable=True)

class CompanyYearInfo(Base) :
    __tablename__ = "company_year_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"))
    year = Column(String, nullable=False)
    current_assets = Column(Integer, nullable=True)
    total_assets = Column(Integer, nullable=True)
    current_liabilities = Column(Integer, nullable=True)
    total_debt = Column(Integer, nullable=True)
    total_capital = Column(Integer, nullable=True)
    revenue = Column(Integer, nullable=True)
    cost_revenue = Column(Integer, nullable=True)
    total_revenue = Column(Integer, nullable=True)
    expenses = Column(Integer, nullable=True)
    operating_profit = Column(Integer, nullable=True)
    net_profit = Column(Integer, nullable=True)

class InteresetCompany(Base) : 
    __tablename__ = "interest_company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("company.id"))
    created_at = Column(DateTime, nullable=False, default=datetime.now)

class Users(Base) :
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    useremail = Column(String, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

class SearchHistory(Base) : 
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_name = Column(String, nullable=False)
    year_list = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
