# app/router/company.py
from fastapi import APIRouter, Depends, Request, UploadFile, File
from ..logic.data_process import DataProcess
from ..logic.calculator import Calculator
from PyPDF2 import PdfReader
from PIL import Image
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.crud import company_crud
from ..db.schema import company_schema
from jose import jwt
from dotenv import load_dotenv
import os, fitz, warnings, re, pytesseract
from statsmodels.tsa.arima.model import ARIMA

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
warnings.filterwarnings("ignore") # warning 에러 안보이게 처리

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
    # 기본으로 보여줄 기업명
    if keyword == "" or keyword is None : 
        result = ["삼성전자", "현대자동차", "기아", "LG전자", "한화엔진", "GS칼텍스", "현대모비스", "HD현대중공업"]
    else :
        data = company_crud.search_company_rename_list(db, keyword)
        result = []
        for item in data : 
            name = item[0]
            if item[1] != None :
                name = name + "(" + item[1] + ")"
            result.append(name)
    
    # 결과값 리턴
    return {
        "status" : "success",
        "data" : result
    }

# 기업 정보 검색 API
# API URL : http://localhost:8000/company/info
# 파라미터 : name | str , Null not able
@router.get("/info")
def company_info(name : str, request : Request, db : Session = Depends(get_db)) : 
    dp = DataProcess()
    company_id = None # compnay_id
    crno = None # 법인등록번호
    
    # 기업명 변경됬는지 확인
    company_name = company_crud.company_name_check(db, name)
    if company_name != None : # 있으면
        new_name = company_name[0] # 새이름
        old_name = company_name[1] # 옛이름
        company_id = company_name[2] # company_id
        
        # 가져온걸로 기업 검색용 이름 찾기
        search_name = company_crud.search_company_info_name(db, name = old_name, name2 = new_name)
        # 있으면 데이터 세팅
        if search_name != None : 
            crno = search_name[1] # 법인등록번호(없을 수도 있음)
            search_name = search_name[0] # 검색용 이름


        data = dp.comapny_info_list(old_name, search_name, crno, new_name) # 공공 데이터 가져오기
    else : 
        # 기업 검색용 이름 찾기
        search_name = company_crud.search_company_info_name(db, name)
        # 있으면 데이터 세팅
        if search_name != None : 
            crno = search_name[1] # 법인등록번호(없을 수도 있음)
            search_name = search_name[0] # 검색용 이름

        data = dp.comapny_info_list(name, search_name, crno) # 데이터 가져오기
    
    # company_id가 있으면
    if company_id != None : 
        data['변경이력'] = [company_name[1], company_name[0]] # 데이터에 변경이력 추가
        company = company_crud.search_company_name(db, id = company_id) # 기업 정보 검색
    else :
        company = company_crud.search_company_name_jongmok(db, name) # 없으면 이름으로 정보 가져오기
    
    # company 정보가 있으면
    if company != None :
        data['종목코드'] = company.jongmok_code # 종목코드
        data['업종코드'] = company.industry_code # 업종코드
        data['업종명'] = company.industry_name # 업종명
        data['company_id'] = company.id # company_id 세팅

        # 로그인 확인
        access_token = request.cookies.get("access_token")
        if not access_token == None : # 로그인 되어있으면
            info = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM) # access_token 값 가져와서
            check = company_crud.check_interest_company(db, user_id=info['id'], company_id=company.id) # 관심기업인지 확인
            if check != None : # 관심기업이면
                data['interest_id'] = check.id # 데이터 세팅

    return {
        "status" : "success",
        "data" : data
    }

# 기업 분석 API
# API URL : http://localhost:8000/company/analyze
# 파라미터 : 
# company_id | str, null not able
# first_year | int, null able
# last_year | int, null able
@router.get("/analyze")
def company_analyze(request : Request, company_id : str, first_year : int = None, last_year : int = None, db : Session = Depends(get_db)) :
    calc = Calculator() # 계산용 class 생성
    company = company_crud.search_company_name(db, id=company_id) # 기업 정보 불러오기
    year_list = company_crud.search_company_year_list(db, company_id=company.id) # 년도 목록 원본 불러오기
    l = list(item[0] for item in year_list) # 년도 목록 생성
        
    # year 입력값 없는 경우
    if  first_year == None or last_year == None :
        result = l # 년도 목록 result 값으로 지정
    else : # year 입력값이 잇으면
        # 입력받은 year로 list 생성
        year_list = list(map(str, list(np.arange(first_year, last_year + 1, 1))))

        # year_list가 6 이상이거나 0 이하 이면
        if len(year_list) >= 6 or len(year_list) <= 0 :
            result = { "msg" : "잘못된 year_list 입니다." } # 에러 띄우기
        else : # 문제 없는 경우
            # 해당 기업의 year 범위 내 재무 정보 목록 가져오기
            schema = company_schema.CompanyYearInfoSearch(company_id=company.id, first_year=str(first_year), last_year=str(last_year), industry_code=None)
            company_data = company_crud.search_company_year_info(db, schema)
            company_info = {
                "업종" : company.industry_code,
                "업종명" : company.industry_name,
                "종목코드" : company.jongmok_code
            }

            # 가져온거 세팅            
            for c_d in company_data : 
                year, d = finance_data_to_dict(c_d) # DB 모델 dict로 변환
                company_info[year] = d # 세팅
            
            # 동일 업종 목록 가져오기
            search_schema = company_schema.CompanyYearInfoSearch(company_id=None, first_year=str(first_year-1), last_year=str(last_year), industry_code=company.industry_code)
            industry_list = company_crud.search_industry_year_info(db, company_year_info_search=search_schema)
            industry_company_list = {} # 목록용 dict 생성
            # for 문으로 돌리기
            for industry in industry_list :
                name = industry[1] # 기업 이름
                year, d = finance_data_to_dict(industry[0]) # 년도랑 해당 년도 정보
                if industry_company_list.get(name) == None : # 해당 기업이 없으면 
                    industry_company_list[name] = {} # 생성하고
                industry_company_list[name][year] = d # 해당 정보 dict에 넣기
            
            # 실제로 계산 가능한지 확인
            if set(year_list).issubset(set(l)) : # 뽑아온 년도 목록안에 해당 년도가 있는지 확인
                result = calc.calc(year_list, company_info, industry_company_list) # 문제 없으면 계산

                # 검색 기록 설정
                access_token = request.cookies.get("access_token") # access_token 가져와서
                if not access_token == None : # 만약 로그인 했다면
                    info = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM) # 해당 정보 가져와서
                    # search_history 생성
                    company_crud.create_search_history(db, company_schema.CompanyHistory(
                        user_id=info['id'],
                        company_id=company.id,
                        company_name = company.name,
                        start_year=str(first_year),
                        end_year=str(last_year)
                    ))

            else : # 계산 불가능하면 검색 결과 없다고 뜨게
                result = { "msg" : "검색결과 없습니다." }
    
    # 값 반환
    return {
        "status" : "success",
        "data" : result
    }

# 기업 예측 API
# API URL : http://localhost:8000/company/prediction
# 파라미터 
# company_id | str, null not able
@router.get("/prediction")
def company_prediction(company_id : str, db : Session = Depends(get_db)) : 
    # 실패용 결과값 미리 준비
    result = { "msg" : "예측이 불가능합니다." }
    
    min_year, max_year = company_crud.max_min_years(db)[0] # db 전체 가장 최근/옛날 년도 가져오기
    prediction_years = list(map(str, list(np.arange(int(max_year) + 1, int(max_year) + 6, 1)))) # 예측치 뽑아낼 년도 목록 뽑기(가장 최근 년도 + 1 한 년도부터 5개년치)
    company = company_crud.search_company_name(db, id=company_id) # 검색한 기업 정보 불러오기
    year_list = company_crud.search_company_year_list(db, company_id=company.id) # 년도 목록 원본 불러오기
    years = list(item[0] for item in year_list) # 년도만 뽑아냄

    # 검색해서 해당 기업의 재무 데이터 가져오기
    schema = company_schema.CompanyYearInfoSearch(company_id=company.id, first_year=str(years[0]), last_year=str(years[len(years)-1]), industry_code=None)
    company_data = company_crud.search_company_year_info(db, schema)

    # 가장 최근 년도 데이터가 없다면 진행하지 않음(이미 폐업했거나 예측할 필요 없는 기업이라고 판단)
    if max_year in years : 
        c_data = {} # 데이터 담을 dict
        # company_data 가져와서 for문으로 돌리기
        for c_d in company_data : 
            year, d = finance_data_to_dict(c_d) # DB 모델 dict로 형변환
            c_data[year] = d # c_data 안에 넣기

        # max_year 부터 예상 5개년치 뽑기
        c_data = company_data_prediction(c_data, int(max_year), int(max_year) + 5)
        # 기타 기업 정보 넣기
        c_data['업종'] = company.industry_code
        c_data['업종명'] = company.industry_name
        c_data['종목코드'] = company.jongmok_code
        
        # 값이 다 있다면 동일 업종 목록도 뽑기
        if c_data != {} :
            # search용 schema 생성
            search_schema = company_schema.CompanyYearInfoSearch(company_id=None, first_year=min_year, last_year=max_year, industry_code=company.industry_code)
            # DB에서 목록 뽑아내기
            industry_list = company_crud.search_industry_year_info(db, company_year_info_search=search_schema)
            # 동일업종 목록용 dict 생성
            industry_company_list = {}
            # for 문 돌려서
            for industry in industry_list :
                name = industry[1] # 기업 이름 건지고
                year, d = finance_data_to_dict(industry[0]) # 해당 년도 재무 정보 dict로 변환
                if industry_company_list.get(name) == None : # 목록 내에 이름이 없으면 생성
                    industry_company_list[name] = {}
                industry_company_list[name][year] = d # 해당 내용 dict에 추가
            
            # 동일 업종 예측치 목록 뽑아내기
            c_i_list = {}
            for i_c_key in industry_company_list.keys() : 
                i_years = list(industry_company_list[i_c_key].keys()) # 해당 기업의 년도 목록 봅아서
                if max_year in i_years : # max_year가 있는지 검사
                    data = company_data_prediction(industry_company_list[i_c_key], int(max_year), int(max_year) + 5) # 있다면 예측치 데이터 생성
                    if data != {} : # 예측치 데이터가 빈값이 아니라면
                        c_i_list[i_c_key] = data # 목록에 넣기

            # 계산용 class 불러와서
            calc = Calculator()
            result = calc.calc(prediction_years, c_data, c_i_list) # result에 계산 값 넣기

    # 결과값 반환
    return {
        "status" : "success",
        "data" : result
    }

# FileOCR API
# API URL : http://localhost:8000/company/fileInfo
@router.get("/fileInfo")
def fileOCRInfo(file: UploadFile = File(...)) : 
    imgPath = r"../OCRImage"
    pdfreader = PdfReader(file)
    pdf_index = pdfreader.pages[0].extract_text()
    pdf_index = pdf_index.replace(".", "")
    pageNum = re.search(r'사업의 개요 ([0-9]+)\n[0-9]+\s[가-힣\s]+([0-9]+)', pdf_index)
    endPageNum = int(pageNum.group(2)) - int(pageNum.group(1))
    pageNum = "Page " + pageNum.group(1) + "\n"
    pass

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

# 재무 정보 model > dict 변환
def finance_data_to_dict(data) :
    # dict key 전환용
    transe_key = {"_sa_instance_state" : "_del", "company_id" :"_del", "year" :"year", "is_visible" : "_del", "id" :"_del", "current_assets" : "유동자산", "total_assets" : "자산총계", "current_liabilities" : "유동부채", "total_debt" : "부채총계", "total_capital" : "자본총계", "revenue" : "매출액", "cost_revenue" : "매출원가", "total_revenue" : "매출총이익", "expenses" : "판매비와관리비", "operating_profit" : "영업이익", "net_profit" : "순이익"}
    d = dict((transe_key[key], value) for (key, value) in data.__dict__.items())
    year = d['year']
    del d['year']
    del d['_del']
    return year, d

# 정해진 년도까지 데이터 예측
def company_data_prediction(data, start_year, end_year) : 
    c_data = {}
    pd.options.display.float_format = '{:.5f}'.format
    df = pd.DataFrame(data)
    for x in list(df.index) : 
        try :
            d_df = df.loc[x, :]
            d_df = d_df.dropna()

            d_df.index = pd.date_range(start=d_df.index[0], periods=len(d_df), freq='YE')

            q1 = d_df.quantile(0.25)  # 1사분위수
            q3 = d_df.quantile(0.75)  # 3사분위수
            iqr = q3 - q1  # IQR

            # 이상치 경계 설정
            lower_bound = q1 - 0.5 * iqr  # 하한
            upper_bound = q3 + 2 * iqr  # 상한

            # 이상치 제거 (하한과 상한을 벗어나는 값 제거)
            d_df = d_df[(d_df >= lower_bound) & (d_df <= upper_bound)]

            indexs = list(d_df.index)

            model = ARIMA(d_df, order=(1, 1, 1))
            model_fit = model.fit()

            step = end_year - int(indexs[len(indexs) - 1].year)
            forecast = model_fit.forecast(steps=step)
            merge_data = pd.concat([d_df, forecast])

            add_index = pd.date_range(start=str(start_year+1), periods=step, freq='YE')
            indexs.extend(add_index)
            merge_data.index = indexs

            for year in range(start_year, end_year+1) : 
                year = str(year)
                key = year + "-12-31"
                if c_data.get(year) == None : 
                    c_data[year] = {}
                c_data[year][x] = int(merge_data[key])
        except Exception as e :
            # print(e)
            pass

    return c_data

@router.get("/data/add/rename") 
def company_rename_add(company_id : int, old_name : str, new_name : str, db : Session = Depends(get_db)) : 
    company_crud.company_rename_new(db , company_id, old_name, new_name) 

@router.get("/data/add/search_name")
def company_search_name(company_id : int, name : str, db : Session = Depends(get_db)) :
    company_crud.create_company_search_name(db, company_id, name)
