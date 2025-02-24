from pydantic import BaseModel

class CompanyCreate(BaseModel) :
    name : str
    jongmok_code : str
    industry_code : str
    industry_name : str

class CompanyInfoCreate(BaseModel) : 
    company_id : int
    year : str
    current_assets : int | None
    total_assets : int | None
    current_liabilities : int | None
    total_debt : int | None
    total_capital : int | None
    revenue : int | None
    cost_revenue : int | None
    total_revenue : int | None
    expenses : int | None
    operating_profit : int | None
    net_profit : int | None

class InterestCompanyCreate(BaseModel) :
    user_id : int
    company_id : int

class CompanyUpdate(CompanyCreate) : 
    id : int

class CompanyInfoUpdate(CompanyInfoCreate) :
    id : int

class CompanyYearInfoSearch(BaseModel) : 
    company_id : int | None
    first_year : str
    last_year : str
    industry_code : str | None
