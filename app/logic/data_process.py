# data_process.py
import json
import pandas as pd
import os
import requests
from dotenv import load_dotenv

# env 파일 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class DataProcess : 
    def __init__(self):
        json_data = self.read_json("process_list") # process_list.json 데이터 가져오기
        self.column_rename = json_data["column_rename"] # 컬럼명 재가공 목록
        self.current_assets = json_data["current_assets"] # 유동 자산 목록
        self.current_liabilities = json_data["current_liabilities"] # 유동 부채 목록
        self.column_list = json_data["column_list"] # 가져올 컬럼 명 목록
        self.company_info = self.info_data() # 회사 정보 목록 가져오기
        self.company_type = self.company_type_list() # 회사 업종 목록 가져오기
        self.company_name_list = {}
        self.company_jongmoc_list = {}

    # json 읽기
    def read_json(self, file_name) : 
        with open("./json/" + file_name + ".json", "r", encoding='UTF-8') as f :
            json_data = json.load(f)

        return json_data

    # 항목명에 따른 당기 내용 재정의
    def type_fixed(self, column, type = "") :
        # 당기인 경우 숫자(str) or NaN(float) 만 있음, 그외의 경우는(항목명, 항목등) str -> int 에서 제외
        if type == "당기" : 
            # 문자인 경우 int 형으로 재정의
            if isinstance(column, str) :
                column = int(column.replace(",", ""))
        # float 형인 경우 NaN이니 "-"으로 값 처리
        if isinstance(column, float) : 
            column = "-"

        return column

    # info data 생성
    def info_data(self, reset = False) : 
        info = {} # 값 넣을 변수
        info_list = ["bs", "pl", "cpl"] # 값 가져올 항목 (bs : 재무상태표, pl : 손익계산서, cpl : 포괄손익계산서)
        
        # company_info.json 이 없거나 reset이 true 인 경우
        if not os.path.isfile("./json/company_info.json") or reset == True : 
            self.company_name_list = {} # 회사 명 목록 초기화
            self.company_jongmoc_list = {} # 회사 종목 목록 초기화

            # 정보 가져오기
            for type in info_list :
                info = self.make_company_info("./download/"+type+"/", type, info)

            # 종목 코드에 맞게 데이터 정리
            for company_jongmoc in self.company_name_list :
                # 만약 해당 종목 코드에 대한 회사명이 2개 이상인 경우 실행
                if len(self.company_name_list[company_jongmoc]) >= 2 :
                    # 회사명 기준은 가장 마지막에 추가된 회사명으로 실행
                    name = list(self.company_name_list[company_jongmoc].keys())[-1]
                    # 종목에대한 회사명 목록 반복문으로 돌리기
                    for j in self.company_name_list[company_jongmoc] :
                        # 이름이 같은 경우는 제외하고
                        if not name == j :
                            # 해당 회사명 안에 있는 년도를 반복문으로 또 돌림
                            for y in self.company_name_list[company_jongmoc][j] :
                                info[name][y] = info[j][y] # 그래서 회사명 기준 이름 항목에다가 해당 년도 데이터 집어넣기
                                info[name] = dict(sorted(info[name].items())) # 키 기준으로 정렬
                                info[j].pop(y, None) # 기존 dict에서 년도 지우기
                            if len(info[j].keys()) <= 3 : # 만약에 해당 회사명 내의 키가 3개 이하(데이터분류, 업종, 업종명 제외 없는 경우) 아예 info 내에서 drop 시키기
                                info.pop(j, None)
            # company_info.json 파일 생성
            with open('./json/company_info.json', 'w', encoding='UTF-8') as f : json.dump(info, f, indent=4, ensure_ascii=False)
        else : # 그 외의 경우 그냥 company_info.json 데이터 가져옴
            info = self.read_json("company_info")

        # company_info 데이터 세팅
        self.company_info = info
        self.company_type_list(True) # 그리고 회사 업종 목록 초기화

        return info

    # company_info.json 생성
    def make_company_info(self, link, file_type, list_data = {}) : 
        entries = os.listdir(link) # 해당 링크의 폴더의 있는 파일들 가져오기
        list = list_data # 데이터 담을 list 생성
        
        # 파일 정보들
        for entry in entries :
            year = entry[0:4] # 파일명에서 년도 추출
            file = pd.read_csv(link + entry, sep = "\t", encoding = "cp949") # encoding이 cp949여서 해당 인코딩으로 가져옴
            data = file.loc[:, file.columns.isin(['회사명', "종목코드", '업종', '업종명', '항목명', '당기', '결산월', '결산기준일'])]  # 해당 컬럼명만 data로 추출
            data = data[data['결산월'] == pd.to_datetime(data['결산기준일']).dt.month] # 결산월 - 결산기준일의 월이 같은 경우만 가져오기(중간에 바뀐 경우 값이 중복되어 들어가 있음. 그런 경우를 배제하기 위함)
            company_list = data.loc[:,'회사명'].drop_duplicates() # 회사명 목록 뽑기(중복제거)
            # company_list = data.loc[data["회사명"] == "삼성전자"]["회사명"].drop_duplicates()

            # 회사별 정보
            for company in company_list :
                d = data[data['회사명'] == company] # 해당 회사명 데이터 추출
                if list.get(company) == None : # 만약 list 안에 없으면 빈 값 생성
                    list[company] = {}

                info = {} # 해당 년도에 대한 데이터 저장용 변수
                if not list[company].get(year) == None : # 만약에 기존 데이터가 있으면 거기에 추가
                    info = list[company][year]

                # 직접 해당 항목에 대한 값 저장 용도
                bebuchae = 0 # 비부동부채
                yudongbuchae = 0 # 유동부채
                yudongjasan = 0 # 유동자산
                soun = 0 # 법인세차감전순손익
                bubinse = 0 # 법인세

                # 포괄손익계산서 일때, 손익계산서의 모든 항목이 있으면 건너뛰기
                if file_type == "cpl" and (info.get("매출총이익") and info.get("매출액") and info.get("영업이익") and info.get("순이익") and info.get("매출원가") and info.get("판매비와관리비")) :
                    continue

                # 항목별 정보
                for idx, ser in d.iterrows() :
                    ser['항목명'] = self.type_fixed(ser['항목명']) # 항목명 nan 제거
                    ser['항목명'] = ser['항목명'].replace(" ", "") # 항목명 공백제거
                    ser['당기'] = self.type_fixed(ser['당기'], "당기") # 당기 데이터 타입 변환
                    company_type = self.type_fixed(ser['업종']) # 업종 데이터 타입 변환
                    company_type_name = self.type_fixed(ser['업종명']) # 업종명 데이터 타입 변환
                    
                    # 이름 재정의
                    if not self.column_rename.get(ser['항목명']) == None :
                        ser['항목명'] = self.column_rename[ser['항목명']]

                    # 재무상태표 한정 실행
                    if file_type == "bs" : 
                        # 유동자산 더하기
                        if ser['항목명'] in self.current_assets and not ser["당기"] == "-":
                            yudongjasan += ser['당기']

                        # 유동부채 더하기
                        if ser['항목명'] in self.current_liabilities and not ser["당기"] == "-":
                            yudongbuchae += ser['당기']
                        
                        # 비유동부채 관련 로직
                        if ser['항목명'] == "비유동부채" and not ser["당기"] == "-":
                            bebuchae = ser['당기']

                    # 손익계산서 or 포괄손익계산서 한정 실행
                    if file_type == "pl" or file_type == "cpl" :
                        # 법인세차감전순이익 관련 로직
                        if ser['항목명'] in ["법인세비용차감전순이익(손실)", "법인세비용차감전당기순이익"] :
                            soun = ser['당기']
                        # 법인세 관련 로직
                        if ser['항목명'] in ["법인세비용(이익)", "법인세비용"] :
                            bubinse = ser['당기']

                    # 항목명 목록에있고 값이 int형인 경우 추가
                    if ser['항목명'] in self.column_list and isinstance(ser['당기'], int) :
                        info[ser['항목명']] = ser['당기']

                # 재무상태표 한정 실행
                if file_type == "bs" : 
                    # 자본 총계는 없는데 자산총계랑 부채총계가 있는 경우 자본총계 계산
                    if info.get("자본총계") == None and (not info.get("자산총계") == None and not info.get("부채총계") == None) :
                        info['자본총계'] = info['자산총계'] - info['부채총계']

                    # 부채총계가 없는데 자산총계와 자본총계가 있는 경우 부채총계 계산
                    if info.get("부채총계") == None and (not info.get("자산총계") == None and not info.get("자본총계") == None) :
                        info['부채총계'] = info['자산총계'] - info['자본총계']
                    
                    # 자산총계가 값이 없는데 자본총계와 부채총계가 있는 경우 자산총계 계산
                    if info.get("자산총계") == None and not info.get("자본총계") == None and not info.get("부채총계") == None :
                        info['자산총계'] = info["자본총계"] + info['부채총계']

                    # 유동부채가 없는데 비부동부채가 값이 있고 부채총계가 있는 경우 계산해서 유동부채 계산
                    if info.get("유동부채") == None and (not bebuchae == 0 and not info.get("부채총계") == None) :
                        info['유동부채'] = info['부채총계'] - bebuchae

                    # 유동부채가 값이 없는 경우 계산한 유동부채 값으로 해결
                    if info.get("유동부채") == None and not yudongbuchae == 0 :
                        info['유동부채'] = yudongbuchae

                    # 유동자산이 값이 없는 경우 계산한 유동자산 값으로 해결
                    if info.get("유동자산") == None and not yudongjasan == 0 :
                        info['유동자산'] = yudongjasan

                    # 필수값이 다 없는 경우 회사 이름 출력
                    # if (info.get("유동자산") == None or info.get("유동부채") == None or info.get("부채총계") == None or info.get("자본총계") == None or info.get("자산총계") == None) :
                    #     print(company)

                # 손익계산서 한정 실행
                if file_type == "pl" : 
                    # 매출액이 없는데 매출총이익과 매출원가가 있는 경우 매출액 계산
                    if info.get("매출액") == None and (not info.get("매출총이익") == None and not info.get("매출원가") == None ) :
                        info['매출액'] = info['매출총이익'] + info['매출원가']

                    # 순이익이 없고 법인세차감전순이익과 법인세가 있는 경우 순이익 계산
                    if info.get("순이익") == None and not bubinse == 0 and not soun == 0 :
                        info["순이익"] = soun - bubinse

                    # 영업이익과 순이익이 없는 경우 회사 이름 출력
                    # if info.get('영업이익') == None or info.get('순이익') == None :
                    #     print(company)

                # 해당 년도에 대해 데이터가 아무것도 없다면 해당 년도 데이터 생성 X
                if info == {} :
                    continue

                # 종목코드 추출
                jongmoc = d.loc[:, '종목코드'].drop_duplicates(ignore_index = True)[0]

                # 종목코드 Null 이 아닌경우
                if not jongmoc == "[null]" :
                    # 일단 회사 종목 리스트에 추가
                    self.company_jongmoc_list[company] = jongmoc
                    # 회사명 목록에 없으면 종목항목 생성
                    if self.company_name_list.get(jongmoc) == None :
                        self.company_name_list[jongmoc] = {}
                    # 회사명 목록에 회사명이 없으면 그것도 추가
                    if self.company_name_list[jongmoc].get(company) == None : 
                        self.company_name_list[jongmoc][company] = []
                    # 해당 년도 데이터에 해당하는 곳으로 데이터 추가
                    if not year in self.company_name_list[jongmoc][company] : 
                        self.company_name_list[jongmoc][company].append(year)
                else : 
                    # null 이긴한데 회사 종목 리스트에 회사명이 있고 회사 명 리스트에 해당 종목에 대한 년도 데이터가 없으면 추가
                    if self.company_jongmoc_list.get(company) and not year in self.company_name_list[self.company_jongmoc_list[company]][company] :
                        self.company_name_list[self.company_jongmoc_list[company]][company].append(year)

                data_type = ""
                if file_type == "CPL" :
                    data_type = "포괄손익계산서"
                # 년도별 회사 정보 넣기
                list[company]['데이터분류'] = data_type
                list[company]['업종'] = company_type
                list[company]['업종명'] = company_type_name
                list[company][year] = info

        return list
    
    # open api get방식으로 request 호출
    def request_open_api(self, url, param) : 
        res = requests.get(url + param)
        return res

    # 기업 정보 가져오기
    def comapny_info_list(self, company_name) :
        # 알파벳 대응 한글 목록
        eng_to_ko = {
            "A" : "에이",
            "B" : "비",
            "C" : "씨",
            "D" : "디",
            "E" : "이",
            "F" : "에프",
            "G" : "지",
            "H" : "에이치",
            "I" : "아이",
            "J" : "제이",
            "K" : "케이",
            "L" : "엘",
            "M" : "엠",
            "N" : "엔",
            "O" : "오",
            "P" : "피",
            "Q" : "큐",
            "R" : "알",
            "S" : "에스",
            "T" : "티",
            "U" : "유",
            "V" : '브이',
            "W" : "더블유",
            "X" : "엑스",
            "Y" : "와이",
            "Z" : "제트" 
        }

        data = {}

        # 공공데이터 API 호출
        url = "http://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2/getCorpOutline_V2"
        param = "?serviceKey=" + os.environ["API_SERVICE_KEY"] +"&pageNo=1&numOfRows=30&resultType=json&corpNm="

        # response 값 가져오기
        res = self.request_open_api(url, param + company_name)
        if res.status_code == 200 : # response가 200 == 성공적이라면
            items = res.json()['response']['body']['items'] # items 내에서
            # 반복문으로 정보들 호출
            for item in items['item'] : 
                if item["enpPbanCmpyNm"] == company_name :  # 기업공시 회사명이랑 같은지 확인
                    data = {
                        "법인등록번호" : item["crno"],
                        "법인명" : item["corpNm"],
                        "법인영문명" : item["corpEnsnNm"],
                        "기업공시회사명" : item["enpPbanCmpyNm"],
                        "기업대표자성명" : item["enpRprFnm"],
                        "사업자등록번호" : item["bzno"],
                        "기업기본주소" : item["enpBsadr"],
                        "기업홈페이지URL" : item["enpHmpgUrl"],
                        "기업전화번호" : item["enpTlno"],
                        "기업팩스번호" : item["enpFxno"],
                        "기업설립일자" : item["enpEstbDt"]
                    }
                    break # 반복문 탈출
        
        # 만약 값이 없으면 기업명 - 알파벳 한글 전환해서 한번 더 검색
        if data == {} :
            name = company_name # 바꾸기 용 변수 생성
            # 알파벳 한글 전환
            for key in eng_to_ko.keys() :
                name = name.replace(key, eng_to_ko[key])

            # API 호출
            res = self.request_open_api(url, param + name)
            if res.status_code == 200 : # 값 정상이면
                items = res.json()['response']['body']['items'] # items 내에서
                # 반복문으로 정보들 호출
                for item in items['item'] : 
                    if item["enpPbanCmpyNm"] == company_name : # 기업공시 회사명이랑 같은지 확인
                        data = {
                            "법인등록번호" : item["crno"],
                            "법인명" : item["corpNm"],
                            "법인영문명" : item["corpEnsnNm"],
                            "기업공시회사명" : item["enpPbanCmpyNm"],
                            "기업대표자성명" : item["enpRprFnm"],
                            "사업자등록번호" : item["bzno"],
                            "기업기본주소" : item["enpBsadr"],
                            "기업홈페이지URL" : item["enpHmpgUrl"],
                            "기업전화번호" : item["enpTlno"],
                            "기업팩스번호" : item["enpFxno"],
                            "기업설립일자" : item["enpEstbDt"]
                        }
                        break # 반복문 탈출

        return data

    # company_type.json 생성
    def company_type_list(self, reset = False) : 
        type_list = {}
        # company_type.json이 없거나 reset이 True 이면
        if not os.path.isfile("./json/company_type.json") or reset == True:
            # 기업명 전부 가져와서
            for name in list(self.company_info.keys()) :
                # 기업 데이터 내에서
                info = self.company_info[name]
                if not type_list.get(info["업종"]) : # 업종만 뽑기
                    type_list[info["업종"]] = []
                type_list[info["업종"]].append(name)
            # 그리고 company_type.json 생성
            with open('./json/company_type.json', 'w', encoding='UTF-8') as f : json.dump(type_list, f, indent=4, ensure_ascii=False)
        else : # 있으면 company_type.json 불러오기
            type_list = self.read_json("company_type")
        
        # self.company_type에다가 값넣기
        self.company_type = type_list

        return type_list

    # 특정 업종의 회사 목록 검색
    def search_company_type(self, type_code) :
        type_list = []
        if self.company_type.get(type_code) :
            type_list = self.company_type[type_code]
        
        return type_list

