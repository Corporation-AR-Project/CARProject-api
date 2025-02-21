from pydantic import BaseModel

class CompanyCreate(BaseModel) :
    name : str
    jongmok_code : str
    industry_code : str
    industry_name : str

class CompanyInfoCreate(BaseModel) : 
    company_id : int
    year : str
    current_assets : int
    total_assets : int
    current_liabilities : int
    total_debt : int
    total_capital : int
    revenue : int
    cost_revenue : int
    total_revenue : int
    expenses : int
    operating_profit : int
    net_profit : int

class InterestCompanyCreate(BaseModel) :
    user_id : int
    company_id : int

