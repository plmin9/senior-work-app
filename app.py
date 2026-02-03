import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_js_eval import get_geolocation
import datetime

# ==========================================
# 1. 설정 정보 (본인의 정보로 꼭 수정하세요)
# ==========================================
SHEET_ID = "1lhCgIWvcn6QrQRKbzrFrU1tPaKtQr3c8GJ-i8hbCsEQ" 
JSON_KEY = "key.json"

st.set_page_config(page_title="노인일자리 관리시스템", layout="centered")

# 구글 시트 연결 함수
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Secrets 금고에 설정값이 있는지 확인
    if "gcp_service_account" in st.secrets:
        import json
        # 문자열로 된 Secrets를 파이썬 딕셔너리(JSON) 형태로 변환
        key_dict = json.loads(st.secrets["gcp_service_account"])
        
        # [수정된 부분] from_json_dict -> from_json_keyfile_dict 로 변경
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    else:
        # 내 컴퓨터에서 실행할 때 (key.json 파일 사용)
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEY, scope)
        
    return gspread.authorize(creds)

st.title("👵 노인일자리 출퇴근 시스템")

try:
    # ------------------------------------------
    # 2. 데이터 로드 및 상단 현황판
    # ------------------------------------------
    # Pandas로 명단 및 통계 읽기
    read_url = f"https://docs.google.com/spreadsheets/d/1lhCgIWvcn6QrQRKbzrFrU1tPaKtQr3c8GJ-i8hbCsEQ/export?format=csv&gid=0"
    data = pd.read_csv(read_url)
    
    if not data.empty:
        names = data["성함"].unique()
        selected_name = st.selectbox("🙋 성함을 선택해주세요:", names)
        
        # [결재 확인 기능]
        client = get_gspread_client()
        log_sheet = client.open_by_key(SHEET_ID).worksheet("근태로그")
        all_logs_data = log_sheet.get_all_records()
        
        if all_logs_data:
            all_logs = pd.DataFrame(all_logs_data)
            # '승인여부' 열이 있는지 확인
            if '승인여부' in all_logs.columns:
                user_logs = all_logs[all_logs['성함'] == selected_name]
                if not user_logs.empty:
                    last_status = user_logs.iloc[-1]['승인여부']
                    if last_status == "승인":
                        st.success(f"✅ 관리자 확인: {selected_name}님의 활동이 승인되었습니다!")
                    elif last_status == "반려":
                        st.error("⚠️ 반려: 기록을 확인하고 다시 제출해주세요.")
                    else:
                        st.info("⏳ 관리자가 활동 내용을 검토 중입니다.")

        # 개인별 누적 시간 표시
        user_info = data[data["성함"] == selected_name].iloc[0]
        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("이번 달 근무", f"{user_info['당월근무시간']} / 60시간")
            progress = min(float(user_info['당월근무시간']) / 60, 1.0)
            st.progress(progress)
        with col_b:
            st.metric("남은 연차", f"{user_info['잔여연차']}시간")

        st.divider()

        # ------------------------------------------
        # 3. GPS 및 출퇴근 버튼
        # ------------------------------------------
        st.write("📍 위치 확인 중...")
        loc = get_geolocation()
        
        if loc:
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            st.success("✅ 위치 확인 완료")

            st.subheader("📝 활동 기록")
            work_types = st.multiselect("업무 선택:", ["상담", "홍보", "환경정비", "교육", "기타"])
            work_memo = st.text_area("상세 내용(공란):", placeholder="특이사항을 입력하세요.")

            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 출근하기", use_container_width=True):
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    summary = f"[{', '.join(work_types)}] {work_memo}"
                    # 데이터 저장 (마지막 열에 '대기' 상태 추가)
                    log_sheet.append_row([selected_name, now, "출근", lat, lon, summary, "대기"])
                    st.balloons()
                    st.info(f"출근 기록 완료! ({now})")
            
            with col2:
                if st.button("🏠 퇴근하기", use_container_width=True):
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    summary = f"[{', '.join(work_types)}] {work_memo}"
                    log_sheet.append_row([selected_name, now, "퇴근", lat, lon, summary, "대기"])
                    st.warning(f"퇴근 기록 완료! ({now})")
        else:
            st.info("💡 위치 권한을 허용해주시면 버튼이 나타납니다.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
    st.info("💡 구글 시트에 '승인여부' 열이 있는지, 명단에 데이터가 있는지 확인해주세요.")

st.divider()

st.caption("관리자가 시트에서 '승인'을 입력하면 어르신 화면에 즉시 반영됩니다.")

