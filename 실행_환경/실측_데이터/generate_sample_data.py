#!/usr/bin/env python3
"""
가상 기업(대한제조정밀) 원천 데이터셋 생성기
ERP, CRM, MES 3대 사일로 시스템의 가상 원천 데이터를 CSV로 생성한다.
일부러 현실적인 키 불일치, 오탈자, 표기 차이, 동일 기업 다중 등록 노이즈를 포함한다.
"""

import os
import csv
import random

def generate_datasets(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    random.seed(42)

    # 1. ERP 원천: 고객사 및 수주 마스터
    erp_customers = [
        {"erp_id": "ERP_CUST_101", "biz_no": "101-81-00234", "name": "현대자동차(주)", "address": "울산광역시 북구 염포로 700", "status": "ACTIVE"},
        {"erp_id": "ERP_CUST_102", "biz_no": "202-82-11456", "name": "기아 주식회사", "address": "서울특별시 서초구 헌릉로 12", "status": "ACTIVE"},
        {"erp_id": "ERP_CUST_103", "biz_no": "303-83-22567", "name": "삼성전자(주)", "address": "경기도 수원시 영통구 삼성로 129", "status": "ACTIVE"},
        {"erp_id": "ERP_CUST_104", "biz_no": "404-84-33678", "name": "LG에너지솔루션", "address": "서울특별시 영등포구 여의대로 108", "status": "ACTIVE"},
        {"erp_id": "ERP_CUST_105", "biz_no": "505-85-44789", "name": "SK온(주)", "address": "서울특별시 종로구 종로 26", "status": "ACTIVE"},
        {"erp_id": "ERP_CUST_106", "biz_no": "606-86-55890", "name": "글로벌정밀기계", "address": "경상남도 창원시 성산구 공단로 50", "status": "ACTIVE"},
        {"erp_id": "ERP_CUST_107", "biz_no": "707-87-66901", "name": "한국부품테크", "address": "인천광역시 남동구 남동서로 200", "status": "SUSPENDED"},
    ]

    erp_file = os.path.join(output_dir, "erp_customers.csv")
    with open(erp_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["erp_id", "biz_no", "name", "address", "status"])
        writer.writeheader()
        writer.writerows(erp_customers)

    # 2. CRM 원천: 영업 계정 및 거래처 (표기 차이 및 중복 존재)
    crm_accounts = [
        {"crm_id": "CRM_ACC_8801", "tax_id": "1018100234", "account_name": "현대자동차 울산공장", "rep_name": "김도윤", "city": "울산"},
        {"crm_id": "CRM_ACC_8802", "tax_id": "2028211456", "account_name": "기아자동차 화성공장", "rep_name": "이서준", "city": "화성"},
        {"crm_id": "CRM_ACC_8803", "tax_id": "3038322567", "account_name": "(주)삼성전자 반도체", "rep_name": "박하은", "city": "수원"},
        {"crm_id": "CRM_ACC_8804", "tax_id": "4048433678", "account_name": "LG엔솔 오창", "rep_name": "최지호", "city": "청주"},
        {"crm_id": "CRM_ACC_8805", "tax_id": "5058544789", "account_name": "에스케이온", "rep_name": "정예린", "city": "서울"},
        {"crm_id": "CRM_ACC_8806", "tax_id": "999-99-99999", "account_name": "현대자동차 남양연구소", "rep_name": "김연구", "city": "화성"},  # 모호 구간 (HITL 대상)
        {"crm_id": "CRM_ACC_8807", "tax_id": "888-88-88888", "account_name": "동양모빌리티", "rep_name": "박동양", "city": "부산"},  # 독립 분리 대상
    ]

    crm_file = os.path.join(output_dir, "crm_accounts.csv")
    with open(crm_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["crm_id", "tax_id", "account_name", "rep_name", "city"])
        writer.writeheader()
        writer.writerows(crm_accounts)

    # 3. MES 원천: 공장, 설비 및 작업 지시
    mes_orders = [
        {"order_id": "ORD-2026-A", "work_order": "WO-9021", "customer_erp_id": "ERP_CUST_101", "product_name": "EV배터리팩 케이스", "amount": 1250000000, "machine_id": "CNC-04", "factory": "울산 1공장", "status": "IN_PROGRESS", "valid_from": "2026-03-01T08:00:00Z", "valid_to": ""},
        {"order_id": "ORD-2026-B", "work_order": "WO-9022", "customer_erp_id": "ERP_CUST_102", "product_name": "차량용 알루미늄 샤시", "amount": 840000000, "machine_id": "PRESS-02", "factory": "화성 2공장", "status": "COMPLETED", "valid_from": "2026-02-10T08:00:00Z", "valid_to": "2026-02-28T18:00:00Z"},
        {"order_id": "ORD-2026-C", "work_order": "WO-9023", "customer_erp_id": "ERP_CUST_103", "product_name": "서버용 방열 모듈", "amount": 2100000000, "machine_id": "LASER-01", "factory": "구미 1공장", "status": "IN_PROGRESS", "valid_from": "2026-03-05T09:00:00Z", "valid_to": ""},
        {"order_id": "ORD-2026-D", "work_order": "WO-9024", "customer_erp_id": "ERP_CUST_104", "product_name": "원통형 배터리 캔", "amount": 670000000, "machine_id": "CNC-07", "factory": "울산 1공장", "status": "IDLE", "valid_from": "2026-03-10T08:00:00Z", "valid_to": ""},
    ]

    mes_file = os.path.join(output_dir, "mes_work_orders.csv")
    with open(mes_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["order_id", "work_order", "customer_erp_id", "product_name", "amount", "machine_id", "factory", "status", "valid_from", "valid_to"])
        writer.writeheader()
        writer.writerows(mes_orders)

    print(f"[성공] 가상 원천 데이터셋 3종 생성 완료: {output_dir}")

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    generate_datasets(base)
