from ..models import Company, CompanyYearInfo, SearchHistory
from ..schema.company_schema import CompanyCreate, CompanyInfoCreate, CompanyUpdate, CompanyInfoUpdate, CompanyYearInfoSearch, CompanyHistory
from sqlalchemy.orm import Session
from sqlalchemy import update

# 기업 생성
def create_company(db : Session, company_create : CompanyCreate) :
    db_company = Company(
        name = company_create.name,
        jongmok_code = company_create.jongmok_code,
        industry_code = company_create.industry_code,
        industry_name = company_create.industry_name
    )
    db.add(db_company)
    db.commit()

# 기업 년도별 정보 생성
def create_company_year_info(db : Session, company_year_info_create : CompanyInfoCreate) :
    db_comapny_info = CompanyYearInfo(
        company_id = company_year_info_create.company_id,
        year = company_year_info_create.year,
        current_assets = company_year_info_create.current_assets,
        total_assets = company_year_info_create.total_assets,
        current_liabilities = company_year_info_create.current_liabilities,
        total_debt = company_year_info_create.total_debt,
        total_capital = company_year_info_create.total_capital,
        revenue = company_year_info_create.revenue,
        cost_revenue = company_year_info_create.cost_revenue,
        total_revenue = company_year_info_create.total_revenue,
        expenses = company_year_info_create.expenses,
        operating_profit = company_year_info_create.operating_profit,
        net_profit = company_year_info_create.net_profit
    )
    db.add(db_comapny_info)
    db.commit()

# 기업 업데이트
def update_company(db : Session, company_update : CompanyUpdate) :
    stmt = (
        update(Company)
        .where(
            Company.id == company_update.id
        )
        .values(
            name = company_update.name,
            jongmok_code = company_update.jongmok_code,
            industry_code = company_update.industry_code,
            industry_name = company_update.industry_name
        )
    )
    db.execute(stmt)
    db.commit()

# 기업 년도별 정보 업데이트
def update_company_year_info(db : Session, company_year_info_update : CompanyInfoUpdate) :
    stmt = (
        update(CompanyYearInfo)
        .where(
            CompanyYearInfo.id == company_year_info_update.id
        )
        .values(
            current_assets = company_year_info_update.current_assets,
            total_assets = company_year_info_update.total_assets,
            current_liabilities = company_year_info_update.current_liabilities,
            total_debt = company_year_info_update.total_debt,
            total_capital = company_year_info_update.total_capital,
            revenue = company_year_info_update.revenue,
            cost_revenue = company_year_info_update.revenue,
            total_revenue = company_year_info_update.total_revenue,
            expenses = company_year_info_update.expenses,
            operating_profit = company_year_info_update.operating_profit,
            net_profit = company_year_info_update.net_profit
        )
    )
    db.execute(stmt)
    db.commit()

# 기업 단일 검색
def search_company_name(db : Session, id : int) : 
    return db.query(Company).filter(Company.id == id).first() 

# 기업 단일 검색(이름 + 종목코드)
def search_company_name_jongmok(db : Session, name : str) : 
    return db.query(Company).filter(Company.name == name).first() 

# 기업 목록 검색
def search_company_name_list(db : Session, keyword : str) : 
    return db.query(Company.name).filter(Company.name.ilike('%' + keyword + '%')).limit(8).all()

# 기업 년도 리스트 검색
def search_company_year_list(db : Session, company_id : int) :
    return db.query(CompanyYearInfo.year).filter(CompanyYearInfo.company_id == company_id).all()

# 기업 년도 정보 검색
def search_company_year(db : Session, company_id : int, year : str) :
    return db.query(CompanyYearInfo).filter(CompanyYearInfo.company_id == company_id, CompanyYearInfo.year == year).first()

# 기업 특정 기간 정보 검색
def search_company_year_info(db : Session, company_year_info_search : CompanyYearInfoSearch) : 
    return db.query(CompanyYearInfo).filter(
        CompanyYearInfo.company_id == company_year_info_search.company_id, 
        CompanyYearInfo.year >= company_year_info_search.first_year, 
        CompanyYearInfo.year <= company_year_info_search.last_year
        ).all()

# 특정 업종 기업의 기간 정보 검색
def search_industry_year_info(db : Session, company_year_info_search : CompanyYearInfoSearch) : 
    return db.query(CompanyYearInfo, Company.name).join(Company).filter(
        Company.industry_code == company_year_info_search.industry_code,
        Company.id == CompanyYearInfo.company_id,
        CompanyYearInfo.year >= company_year_info_search.first_year, 
        CompanyYearInfo.year <= company_year_info_search.last_year
    ).all()

# 검색 기록 저장
def create_search_history(db : Session, create_history : CompanyHistory) : 
    db_search_history = SearchHistory(
        user_id = create_history.user_id,
        company_id = create_history.company_id,
        company_name = create_history.company_name,
        start_year = create_history.start_year,
        end_year = create_history.end_year
    )
    db.add(db_search_history)
    db.commit()