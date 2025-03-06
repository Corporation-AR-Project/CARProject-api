# calculator.py
from .data_process import DataProcess
import numpy as np

class Calculator : 
    def __init__(self):
        pass

    # 기업 재무 정보 계산 및 분석
    def calc(self, year_list, company_info, industry_company_list) : 
        result = {}
        # 년도 목록 반복문 돌리기
        for year in year_list :
            type_name = company_info['업종명'] # 업종명
            calc_result = self.year_data_calc(company_info, year) # 계산 결과 값
            type_result = self.year_type_data_calc(industry_company_list, year) # 업종별 분석 값
            type_result["업종명"] = type_name

            # 해당 년도에 대한 결과 세팅
            result[year] = {
                "계산결과" : calc_result,
                "세무정보" : company_info[year],
                "동종업계" : type_result
            }

        return result

    # 업종별 기업들의 재무 정보 계산 결과 값
    def year_type_data_calc(self, industry_company_list, year) :
        # 결과 dict 세팅
        result_list = {
            "매출총이익률" : [],
            "영업이익률" : [],
            "순이익률" : [],
            "매출원가및판관비" : []
        }
        # 변화율 계산용 dict
        trend_result_list = {
            "매출총이익률" : [],
            "영업이익률" : [],
            "순이익률" : [],
            "매출원가및판관비" : []
        }
        
        # 해당하는 업종의 회사 목록 불러오기
        type_list = industry_company_list.keys()
        
        # 해당하는 업종의 회사에 대한 계산 값 구하기
        for name in type_list : 
            # 회사 정보
            type_company = industry_company_list[name]
            # 해당하는 년도에 대한 값이 있으면
            if not type_company.get(year) == None : 
                calc_result = self.year_data_calc(type_company, year) # 계산값 구하기
                one_year_calc_result = {} # 직전년도 값 변수 세팅

                # 직전년도 값이 있는지 확인 후 값 세팅
                if type_company.get(str(int(year) - 1)) :
                    one_year_calc_result = self.year_data_calc(type_company, str(int(year) - 1))

                # 평균 구하기
                # 매출총이익률
                if not calc_result.get("매출총이익률") == None :
                    result_list["매출총이익률"].append(calc_result["매출총이익률"])

                # 영업이익률
                if not calc_result.get("영업이익률") == None :
                    result_list["영업이익률"].append(calc_result["영업이익률"])

                # 순이익률
                if not calc_result.get("순이익률") == None :
                    result_list["순이익률"].append(calc_result["순이익률"])

                # 매출 원가 및 판관비 계산용 변수
                wonga = 0
                # 매출원가
                if not type_company[year].get("매출원가") == None : 
                    wonga += type_company[year]["매출원가"]

                # 판관비
                if not type_company[year].get("판매비와관리비") == None :
                    wonga += type_company[year]["판매비와관리비"]

                # 매출원가 + 판관비 있는지 체크
                if not type_company[year].get("매출원가") == None or not type_company[year].get("판매비와관리비") == None : # 매출원가 or 판관비 중 하나라도 잇다면
                    result_list["매출원가및판관비"].append(wonga)
                
                # 변화율 계산
                if not one_year_calc_result == {} :
                    # 매출총이익률 ((당해 매출총이익률 - 직전 매출총이익률) / 직전 매출총이익률 * 100)
                    if calc_result.get("매출총이익률") != None and one_year_calc_result.get("매출총이익률") != None and one_year_calc_result["매출총이익률"] != 0 :
                        trend_result_list["매출총이익률"].append((calc_result["매출총이익률"] - one_year_calc_result["매출총이익률"]) / one_year_calc_result["매출총이익률"] * 100)

                    # 영업이익률 ((당해 영업이익률 - 직전 영업이익률) / 직전 영업이익률 * 100)
                    if calc_result.get("영업이익률") != None and one_year_calc_result.get("영업이익률") != None and one_year_calc_result["영업이익률"] != 0 :
                        trend_result_list["영업이익률"].append((calc_result["영업이익률"] - one_year_calc_result["영업이익률"]) / one_year_calc_result["영업이익률"] * 100)

                    # 순이익률 ((당해 순이익률 - 직전 순이익률) / 직전 순이익률 * 100)
                    if calc_result.get("순이익률") != None and one_year_calc_result.get("순이익률") != None and one_year_calc_result["순이익률"] != 0 :
                        trend_result_list["순이익률"].append((calc_result["순이익률"] - one_year_calc_result["순이익률"]) / one_year_calc_result["순이익률"] * 100)

                    # 매출 원가 및 판관비 계산용 변수
                    last_wonga = 0
                    # 매출원가
                    if type_company.get(str(int(year) - 1)) != None and type_company[str(int(year) - 1)].get("매출원가") != None :
                        last_wonga += type_company[str(int(year) - 1)]["매출원가"]

                    # 판관비
                    if type_company.get(str(int(year) - 1)) != None and type_company[str(int(year) - 1)].get("판매비와관리비") != None :
                        last_wonga += type_company[str(int(year) - 1)]["판매비와관리비"]

                    # 매출원가 + 판관비 있는지 체크
                    if not wonga == 0 and not last_wonga == 0 : # 둘다 0이 아니면 ((당해 원가 - 직전 원가) / 직전 원가 * 100)
                        trend_result_list["매출원가및판관비"].append((wonga - last_wonga) / last_wonga * 100)
        # 값 세팅
        type_result = {
            "평균" : {}, 
            "중위값" : {},
            "추세" : {}
        }

        if not (result_list["매출총이익률"] == [] or result_list["순이익률"] == [] or result_list["영업이익률"] == [] or result_list["매출원가및판관비"] == []) :
            type_result["평균"] = {
                "매출총이익률" : round(np.mean(result_list["매출총이익률"]), 2),
                "영업이익률" : round(np.mean(result_list["영업이익률"]), 2),
                "순이익률" : round(np.mean(result_list["순이익률"]), 2),
                "매출원가및판관비" : round(np.mean(result_list["매출원가및판관비"])),
            }

            type_result["중위값"] = {
                "매출총이익률" : round(np.median(result_list["매출총이익률"]), 2),
                "영업이익률" : round(np.median(result_list["영업이익률"]), 2),
                "순이익률" : round(np.median(result_list["순이익률"]), 2),
                "매출원가및판관비" : round(np.median(result_list["매출원가및판관비"])),
            }

        # 변화율 항목이 전부 빈 값이 아니면 추세 데이터 생성
        if not (trend_result_list["매출총이익률"] == [] or trend_result_list["순이익률"] == [] or trend_result_list["영업이익률"] == [] or trend_result_list["매출원가및판관비"] == []) :
            type_result["추세"] = {
                "매출총이익률" : round(np.median(trend_result_list["매출총이익률"]), 2),
                "영업이익률" : round(np.median(trend_result_list["영업이익률"]), 2),
                "순이익률" : round(np.median(trend_result_list["순이익률"]), 2),
                "매출원가및판관비변화율" : round(np.median(trend_result_list["매출원가및판관비"])),
            }

        return type_result

    # 각종 비율 계산
    def year_data_calc(self, info, year) : 
        data = info[year] # 해당 년도에 대한 재무 정보 세팅
        calc_result = {} # 결과값 세팅

        # 계산
        # 유동비율 계산 (유동자산 / 유동부채 * 100)
        if data.get("유동자산") != None and data.get("유동부채") != None : 
            calc_result["유동비율"] = round(data["유동자산"] / data["유동부채"] * 100, 2)
        # 부채비율 계산 (부채총계 / 자본총계 * 100)
        if data.get("부채총계") != None and data.get("자본총계") != None :
            calc_result["부채비율"] = round(data["부채총계"] / data["자본총계"] * 100, 2)
        # 자본총계 계산 (자본총계 / 자산총계 * 100)
        if data.get("자본총계") != None and data.get("자산총계") != None : 
            calc_result["자기자본비율"] = round(data["자본총계"] / data["자산총계"] * 100, 2)
        # 매출총이익률 계산 (매출총이익 / 매출액 * 100)
        if data.get("매출총이익") != None and data.get("매출액") != None :
            calc_result["매출총이익률"] = round(data["매출총이익"] / data["매출액"] * 100, 2)
        # 영업이익 계산 (영업이익 / 매출액 * 100)
        if data.get("영업이익") != None and data.get("매출액") != None :
            calc_result["영업이익률"] = round(data["영업이익"] / data["매출액"] * 100, 2)
        # 순이익률 계산 (순이익 / 매출액 * 100)
        if data.get("순이익") != None and data.get("매출액") != None :
            calc_result["순이익률"] = round(data["순이익"] / data["매출액"] * 100, 2)

        return calc_result
