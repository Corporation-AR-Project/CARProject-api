# CARProject-api (Corporate Analysis Report - API)
글로벌 아카데미 차세대 AI 예측 Solution 개발(Java, Python) (5회차) - 1조 프로젝트 : 기업분석리포트 프로젝트 API

## 📌 프로젝트 소개
기업분석리포트 프로젝트는 [전자공시시스템](https://dart.fss.or.kr/main.do)(DART : Data Analysis, Retrieval and Transfer System)의 정보를 활용하여 기업의 재무정보를 분석 및 예측하여 누구나 쉽게 파악할 수 있는 보고서를 제공하는 사이트를 제작하는 것을 목표로 하고 있습니다.

해당 repository 에서는 프로젝트의 API 부분을 관리하고 있습니다.

## 📅 개발 기간
+ 총 기간 :  2025/03/08 ~ 2025/04/25
    + 기획 및 시스템 설계 : 2025/03/08 ~ 2025/03/09 ✅
    + 데이터 분석 및 정제 : 2025/03/10 ~ 2025/04/04
    + Front-end 설계 및 구현 : 2025/03/07 ~ 2025/04/15
    + Back-end 설계 및 구현 : 2025/03/07 ~ 2025/04/15
    + 프로젝트 테스트 및 발표 : 2025/04/16 ~ 2025/04/25

## 👤 팀 구성
|이름|역할|
|---|--------|
|연지수|(팀장) 기획 및 시스템 설계, Back-end 설계 및 구현|
|김진영|데이터 분석 및 정제, Back-end 구현|
|박수연|Front-end 설계 및 구현|
|장하은|데이터 분석 및 정제, Back-end 구현|

## 개발 환경
+ `python 3.12.8`
+ `FastAPI`
+ `SQLite`

## 실행방법
CARProject-api의 실행방법에 대해 기술합니다.

### Install 
실행 전, 아래 패키지를 Install 합니다.
``` py
# fastapi
pip install fastapi

# uvicorn
pip install uvicorn

# numpy
pip install numpy

# pandas
pip install pandas

# python-dotenv
pip install python-dotenv

# sqlalchemy
pip install sqlalchemy

# alembic
pip install alembic

# pydantic[email]
pip install "pydantic[email]"

# passlib[bcrypt]
pip install "passlib[bcrypt]"

# python-multipart
pip install python-multipart

# python-jose[cryptography]
pip install "python-jose[cryptography]"

# sklearn
pip install -U scikit-learn
```

### Run
SQLite DB 생성
```
alembic revision --autogenerate
alembic upgrade head
```

local 환경에서 API를 실행 (기본 port : 8000)
```
uvicorn main:app --reload
```