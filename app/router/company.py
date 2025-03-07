# app/router/company.py
from fastapi import APIRouter, Depends, Request
from ..logic.data_process import DataProcess
from ..logic.calculator import Calculator
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.crud import company_crud
from ..db.schema import company_schema
from jose import jwt
from dotenv import load_dotenv
import os
from statsmodels.tsa.arima.model import ARIMA
import pmdarima as pm
import warnings
warnings.filterwarnings("ignore")

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
def company_info(name : str, request : Request, db : Session = Depends(get_db)) : 
    dp = DataProcess()
    data = dp.comapny_info_list(name) # 데이터 가져오기
    company = company_crud.search_company_name_jongmok(db, name)
    if company != None :
        data['종목코드'] = company.jongmok_code
        data['업종코드'] = company.industry_code
        data['업종명'] = company.industry_name
        data['company_id'] = company.id

        access_token = request.cookies.get("access_token")
        if not access_token == None :
            info = jwt.decode(access_token, SECRET_KEY, algorithms=ALGORITHM)
            check = company_crud.check_interest_company(db, user_id=info['id'], company_id=company.id)
            if check != None :
                data['interest_id'] = check.id

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
            

            search = company_schema.CompanyYearInfoSearch(company_id=None, first_year=str(first_year-1), last_year=str(last_year), industry_code=company.industry_code)
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

# 기업 예측 API
# API URL : http://localhost:8000/company/prediction
# 파라미터 
# company_id | str, null not able
@router.get("/prediction")
def company_prediction(company_id : str, db : Session = Depends(get_db)) : 
    result = {
        "msg" : "예측이 불가능합니다."
    }
    prediction_years = ['2024', '2025', '2026', '2027', '2028']
    company = company_crud.search_company_name(db, id=company_id)
    year_list = company_crud.search_company_year_list(db, company_id=company.id)
    years = []
    for item in year_list :
        years.append(item[0])
    company_data = company_crud.search_company_year_info(db, company_schema.CompanyYearInfoSearch(company_id=company.id, first_year=str(years[0]), last_year=str(years[len(years)-1]), industry_code=None))
    # years.extend(prediction_years)
    if '2023' in years : 
        data = {}
        for d in company_data : 
            data[d.year] = {
                '유동자산' : d.current_assets,
                '자산총계' : d.total_assets,
                '유동부채' : d.current_liabilities,
                '부채총계' : d.total_debt,
                '자본총계' : d.total_capital,
                '매출액' : d.revenue,
                '매출원가' : d.cost_revenue,
                '매출총이익' : d.total_revenue,
                '판매비와관리비' : d.expenses,
                '영업이익' : d.operating_profit,
                '순이익' : d.net_profit
            }
        
        c_data = company_data_prediction(data, years)
        c_data['업종'] = company.industry_code
        c_data['업종명'] = company.industry_name
        c_data['종목코드'] = company.jongmok_code
        
        if c_data != {} :
            search = company_schema.CompanyYearInfoSearch(company_id=None, first_year=str(2015), last_year=str(2023), industry_code=company.industry_code)
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
                
            c_i_list = {}
            for i_c_key in industry_company_list.keys() : 
                i_years = list(industry_company_list[i_c_key].keys())
                if '2023' in i_years : 
                    i_years.extend(prediction_years)
                    data = company_data_prediction(industry_company_list[i_c_key], i_years)
                    if data != {} : 
                        c_i_list[i_c_key] = data

            calc = Calculator()
            result = calc.calc(prediction_years, c_data, c_i_list)


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

# 값을 배열로 만들어서 반환
def return_arr(data) :
    return [int(data)]

# 정해진 년도까지 데이터 예측
def company_data_prediction(data, years) : 
    c_data = {}
    pd.options.display.float_format = '{:.5f}'.format
    df = pd.DataFrame(data)
    x_list = list(df.index)
    for x in x_list : 
    #     d_df = df.loc[x, :]
    #     d_df = d_df.dropna()

    #     get_x = list(map(return_arr, list(d_df.index)))
    #     scaler = StandardScaler()
    #     X_scaled = scaler.fit_transform(get_x)
    #     y = d_df.values

    #    # 훈련 데이터와 테스트 데이터로 분할
    #     # X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=42)

    #     # 릿지 회귀 모델 정의
    #     ridge_model = Ridge(alpha=1.0)  # alpha는 정규화 강도

    #     # 모델 학습
    #     ridge_model.fit(X_scaled, y)

    #     get_x = sorted(list(set(years) - set(list(d_df.index))))
    #     print(get_x)

    #     future_years = pd.DataFrame({'Year': get_x})

    #     # 연도 데이터 표준화
    #     future_years_scaled = scaler.transform(future_years)

    #     # 2024~2028년 자산 변화량 예측
    #     future_predictions = ridge_model.predict(future_years_scaled)
    #     print(future_predictions)

    #     for year, pred in zip(future_years['Year'], future_predictions):
    #         d_df.loc[str(year)] = pred
        
    #     for y in list(d_df.index) : 
    #         if c_data.get(y) == None : 
    #             c_data[y] = {}
    #         c_data[y][x] = int(d_df[y])


        # 모델 성능 평가
        # mse = mean_squared_error(y_test, y_pred)
        # r2 = r2_score(y_test, y_pred)

        # 결과 출력
        # print(f"릿지 회귀 모델 성능:")
        # print(f"평균 제곱 오차(MSE): {mse}")
        # print(f"R² (결정 계수): {r2}")
        # print("\n회귀 계수:")
        # print(ridge_model.coef_)

        try :
            d_df = df.loc[x, :]
            d_df = d_df.dropna()

            d_df.index = pd.date_range(start=d_df.index[0], periods=len(d_df), freq='YE')

            q1 = d_df.quantile(0.25)  # 1사분위수
            q3 = d_df.quantile(0.75)  # 3사분위수
            iqr = q3 - q1  # IQR

            # 이상치 경계 설정
            lower_bound = q1 - 1.5 * iqr  # 하한
            upper_bound = q3 + 1.5 * iqr  # 상한

            # 이상치 제거 (하한과 상한을 벗어나는 값 제거)
            d_df = d_df[(d_df >= lower_bound) & (d_df <= upper_bound)]

            indexs = list(d_df.index)

            # model = pm.auto_arima(d_df, seasonal=False, stepwise=True, trace=True)

            model = ARIMA(d_df, order=(1, 1, 1))
            model_fit = model.fit()

            step = 2028 - int(indexs[len(indexs) - 1].year)
            # forecast = model.predict(n_periods=step)

            forecast = model_fit.forecast(steps=step)

            merge_data = pd.concat([d_df, forecast])

            add_index = pd.date_range(start="2024", periods=step, freq='YE')
            indexs.extend(add_index)

            merge_data.index = indexs


            for y in list(range(2023, 2029)) : 
                key = str(y) + "-12-31"
                if c_data.get(str(y)) == None : 
                    c_data[str(y)] = {}
                c_data[str(y)][x] = int(merge_data[key])
        except Exception as e :
            # print(e)
            pass


    # df = pd.DataFrame(data)
    # x_list = list(df.index)
    # make_df = pd.DataFrame()
    # pd.options.display.float_format = '{:.5f}'.format
    # for x in x_list : 
    #     d_df = df.loc[x, :]
    #     d_df = d_df.dropna()

    #     get_x = sorted(list(map(return_arr, list(set(years) - set(list(d_df.index)))))) 
    #     x_data = list(map(return_arr, list(d_df.index)))
    #     y_data = d_df.values
    #     reg = LinearRegression()
    #     reg.fit(x_data, y_data)
    #     y_pred = reg.predict(get_x)
    #     idx = 0
    #     for y in get_x : 
    #         d_df.loc[str(y[0])] = y_pred[idx]
    #         idx+=1
    #     make_df[x] = d_df
    #     for y in list(d_df.index) : 
    #         if c_data.get(y) == None : 
    #             c_data[y] = {}
    #         c_data[y][x] = int(d_df[y])
    
    return c_data
