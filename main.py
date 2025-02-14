# main.py
# uvicorn main:app --reload

from fastapi import FastAPI, Query # FastAPI import
from pydantic import BaseModel
from typing import List, Union
from data_process import DataProcess
from calculator import Calculator
import numpy as np

app = FastAPI()

# 기본 API
@app.get("/")
def default() : 
    return {
        "status": "success",
        "data": {}
    }

# 기업명 검색 API
# API URL : http://localhost:8000/company/search
# 파라미터 : keyword | str , Null able
@app.get("/company/search")
def search_company_keyword(keyword : str = None) :
    data = []
    # 기본으로 보여줄 기업명
    if keyword == "" or keyword == None : 
        data = ["삼성전자", "현대자동차", "기아", "LG전자", "한화엔진", "GS칼텍스", "현대모비스", "이마트"]
    else :
        dp = DataProcess()
        klist = list(dp.company_info.keys()) # 기업명 목록 뽑아서
        data = [name for name in klist if keyword in name][0:8] # 문자열 검색한 다음에 8개까지 가져오기
    # 결과값 리턴
    return {
        "status" : "success",
        "data" : data
    }

# 기업 정보 검색 API
# API URL : http://localhost:8000/company/info
# 파라미터 : name | str , Null not able
@app.get("/company/info")
def company_info(name : str) : 
    dp = DataProcess()
    data = dp.comapny_info_list(name) # 데이터 가져오기
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
@app.get("/company/analyze")
def company_analyze(name : str, first_year : int = None, last_year : int = None) :
    calc = Calculator()

    # year 입력값 없는 경우
    if first_year == None or last_year == None :
        result = calc.company_year_list(name) # 해당 기업의 year_list 가져오기
    else : 
        # 입력받은 year로 list 생성
        year_list = list(np.arange(first_year, last_year + 1, 1))

        # year_list가 6 이상이거나 0 이하 이면
        if len(year_list) >= 6 or len(year_list) <= 0 :
            result = {
                "msg" : "잘못된 year_list 입니다."
            }
        else : # 문제 없는 경우
            # 실제로 계산 가능한지 확인
            if calc.calc_check(name, year_list) :
                result = calc.calc(name, year_list) # 문제 없으면 계산
            else : # 계산 불가능하면 검색 결과 없다고 뜨게
                result = {
                    "msg" : "검색결과 없습니다."
                }
    
    # 값 반환
    return {
        "status" : "success",
        "data" : result
    }

# 데이터 초기화 API
# API URL : http://localhost:8000/company/data/reset
# 파라미터
# is_working | boolean, null able
@app.get("/company/data/reset")
def company_data_reset(is_working = None) :
    # is_working이 True일때만 동작(잘못 호출했을때 작동하는 것을 방지)
    if is_working == True :
        dp = DataProcess()
        dp.info_data(True)
    return {
        "status" : "success",
        "data" : {}
    }
