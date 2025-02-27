# app/router/company.py
from fastapi import APIRouter, Depends, Request
from ..logic.data_process import DataProcess
from ..logic.calculator import Calculator
import numpy as np
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.crud import company_crud
from ..db.schema import company_schema
from jose import jwt
from dotenv import load_dotenv
import os

# env 파일 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"]) # access_token 종료 기간
SECRET_KEY = os.environ["SECRET_KEY"] # secret_key
ALGORITHM = os.environ["ALGORITHM"] # algorithm

router = APIRouter(
    prefix="/company"
)

# 기업명 검색 API
# API URL : http://localhost:8000/company/search
# 파라미터 : keyword | str , Null able
@router.get("/search")
def search_company_keyword(db : Session = Depends(get_db), keyword : str = None) :
    data = []
    # 기본으로 보여줄 기업명
    if keyword == "" or keyword == None : 
        data = ["삼성전자", "현대자동차", "기아", "LG전자", "한화엔진", "GS칼텍스", "현대모비스", "HD현대중공업"]
    else :
        data = company_crud.search_company_name_list(db, keyword=keyword)
        result = []
        for item in data :
            result.append(item[0])
    # 결과값 리턴
    return {
        "status" : "success",
        "data" : result
    }

# 기업 정보 검색 API
# API URL : http://localhost:8000/company/info
# 파라미터 : name | str , Null not able
@router.get("/info")
def company_info(name : str, db : Session = Depends(get_db)) : 
    dp = DataProcess()
    data = dp.comapny_info_list(name) # 데이터 가져오기
    company = company_crud.search_company_name_jongmok(db, name)
    if company != None :
        data['종목코드'] = company.jongmok_code
        data['업종코드'] = company.industry_code
        data['업종명'] = company.industry_name
        data['company_id'] = company.id
    return {
        "status" : "success",
        "data" : data
    }

# 기업 분석 API
# API URL : http://localhost:8000/company/analyze
# 파라미터 : 
# name | str, null not able
# first_year | int, null able
# last_year | int, null able
@router.get("/analyze")
def company_analyze(request : Request, company_id : str, first_year : int = None, last_year : int = None, db : Session = Depends(get_db)) :
    calc = Calculator()
    company = company_crud.search_company_name(db, id=company_id)
    year_list = company_crud.search_company_year_list(db, company_id=company.id)
    l = []
    for item in year_list :
        l.append(item[0])
        
    # year 입력값 없는 경우
    if  first_year == None or last_year == None :
        result = l
    else : 
        # 입력받은 year로 list 생성
        year_list = list(map(str, list(np.arange(first_year, last_year + 1, 1))))

        # year_list가 6 이상이거나 0 이하 이면
        if len(year_list) >= 6 or len(year_list) <= 0 :
            result = {
                "msg" : "잘못된 year_list 입니다."
            }
        else : # 문제 없는 경우
            company_data = company_crud.search_company_year_info(db, company_schema.CompanyYearInfoSearch(company_id=company.id, first_year=str(first_year), last_year=str(last_year), industry_code=None))
            company_info = {
                "업종" : company.industry_code,
                "업종명" : company.industry_name,
                "종목코드" : company.jongmok_code
            }
            for d in company_data : 
                company_info[d.year] = {
                    "유동자산": d.current_assets,
                    "자산총계": d.total_assets,
                    "유동부채": d.current_liabilities,
                    "부채총계": d.total_debt,
                    "자본총계": d.total_capital,
                    "매출액": d.revenue,
                    "매출원가": d.cost_revenue,
                    "매출총이익": d.total_revenue,
                    "판매비와관리비": d.expenses,
                    "영업이익": d.operating_profit,
                    "순이익": d.net_profit
                }

            search = company_schema.CompanyYearInfoSearch(company_id=None, first_year=str(first_year-1), last_year=str(last_year), industry_code="262")
            industry_list = company_crud.search_industry_year_info(db, company_year_info_search=search)
            industry_company_list = {}
            for industry in industry_list :
                if industry_company_list.get(industry[1]) == None :
                    industry_company_list[industry[1]] = {}
                industry_company_list[industry[1]][industry[0].year] = {
                    "유동자산": industry[0].current_assets,
                    "자산총계": industry[0].total_assets,
                    "유동부채": industry[0].current_liabilities,
                    "부채총계": industry[0].total_debt,
                    "자본총계": industry[0].total_capital,
                    "매출액": industry[0].revenue,
                    "매출원가": industry[0].cost_revenue,
                    "매출총이익": industry[0].total_revenue,
                    "판매비와관리비": industry[0].expenses,
                    "영업이익": industry[0].operating_profit,
                    "순이익": industry[0].net_profit
                }
            
            # 실제로 계산 가능한지 확인
            if set(year_list).issubset(set(l)) :
                result = calc.calc(year_list, company_info, industry_company_list) # 문제 없으면 계산

                access_token = request.cookies.get("access_token")
                if not access_token == None :
                    info = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
                    company_crud.create_search_history(db, company_schema.CompanyHistory(
                        user_id=info['id'],
                        company_id=company.id,
                        company_name = company.name,
                        start_year=str(first_year),
                        end_year=str(last_year)
                    ))

            else : # 계산 불가능하면 검색 결과 없다고 뜨게
                result = {
                    "msg" : "검색결과 없습니다."
                }
    
    # 값 반환
    return {
        "status" : "success",
        "data" : result
    }

# JSON 데이터 초기화 API
# API URL : http://localhost:8000/company/data/reset
# 파라미터
# is_working | boolean, null able
@router.get("/data/reset")
def company_data_reset(is_working = None) :
    # is_working이 True일때만 동작(잘못 호출했을때 작동하는 것을 방지)
    if is_working :
        dp = DataProcess()
        dp.info_data(True)
    return {
        "status" : "success",
        "data" : {}
    }

# DB 데이터 초기화 API
# API URL : http://localhost:8000/company/data/db/reset
# 파라미터
# is_working | boolean, null able
@router.get("/data/db/reset")
def company_db_data_reset(db : Session = Depends(get_db), is_working = None) : 
    dp = DataProcess()
    data = dp.read_json('company_info')
    company_list = data.keys()

    if is_working : 
        for company in company_list : 
            info = data[company]
            company_id = company_crud.search_company_name_jongmok(db, name=company)
            if company_id == None :
                _company_create = company_schema.CompanyCreate(name = company, jongmok_code=info['종목코드'], industry_code=str(info['업종']), industry_name=info['업종명'])
                company_crud.create_company(db, company_create=_company_create)
            else :
                company_id = company_id.id
                _company_update = company_schema.CompanyUpdate(name = company, jongmok_code=info['종목코드'], industry_code=str(info['업종']), industry_name=info['업종명'], id = company_id)
                company_crud.update_company(db, _company_update)

            company_id = company_crud.search_company_name_jongmok(db, name=company).id

            for key in info.keys() :
                if not key in ['데이터분류', '업종', '업종명', '종목코드'] : 
                    year_data = info[key]
                    company_year_id = company_crud.search_company_year(db, company_id=company_id, year = key)
                    if company_year_id == None :
                        _year_info = company_schema.CompanyInfoCreate(
                            company_id=company_id,
                            year=key,
                            current_assets=year_data["유동자산"] if year_data.get("유동자산") else None,
                            total_assets=year_data["자산총계"] if year_data.get("자산총계") else None,
                            current_liabilities=year_data["유동부채"] if year_data.get("유동부채") else None,
                            total_debt=year_data["부채총계"] if year_data.get("부채총계") else None,
                            total_capital=year_data["자본총계"] if year_data.get("자본총계") else None,
                            revenue=year_data["매출액"] if year_data.get("매출액") else None,
                            cost_revenue=year_data["매출원가"] if year_data.get("매출원가") else None,
                            total_revenue=year_data["매출총이익"] if year_data.get("매출총이익") else None,
                            expenses=year_data["판매비와관리비"] if year_data.get("판매비와관리비") else None,
                            operating_profit=year_data["영업이익"] if year_data.get("영업이익") else None,
                            net_profit=year_data["순이익"] if year_data.get("순이익") else None
                        )
                        company_crud.create_company_year_info(db, company_year_info_create=_year_info)
                    else :
                        _year_info = company_schema.CompanyInfoUpdate(
                            company_id=company_id,
                            year=key,
                            current_assets=year_data["유동자산"] if year_data.get("유동자산") else None,
                            total_assets=year_data["자산총계"] if year_data.get("자산총계") else None,
                            current_liabilities=year_data["유동부채"] if year_data.get("유동부채") else None,
                            total_debt=year_data["부채총계"] if year_data.get("부채총계") else None,
                            total_capital=year_data["자본총계"] if year_data.get("자본총계") else None,
                            revenue=year_data["매출액"] if year_data.get("매출액") else None,
                            cost_revenue=year_data["매출원가"] if year_data.get("매출원가") else None,
                            total_revenue=year_data["매출총이익"] if year_data.get("매출총이익") else None,
                            expenses=year_data["판매비와관리비"] if year_data.get("판매비와관리비") else None,
                            operating_profit=year_data["영업이익"] if year_data.get("영업이익") else None,
                            net_profit=year_data["순이익"] if year_data.get("순이익") else None,
                            id = company_year_id.id
                        )
                        company_crud.update_company_year_info(db, company_year_info_update=_year_info)

    return {
        "msg" : "DB 입력이 완료되었습니다."
    }
