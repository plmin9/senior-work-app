import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="근태관리 시스템", layout="wide")

# --- 1. 구글 시트 연결 설정 ---
try:
    s = st.secrets["connections"]["gsheets"]
    key = s["private_key"].replace("\\n", "\n")
    creds_info = {
        "type": "service_account", "project_id": s["project_id"],
        "private_key": key, "client_email": s["service_account_email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet_url = s["spreadsheet"]
    sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    doc = client.open_by_key(sheet_id)
    sheet = doc.get_worksheet(0)
    
    # 데이터 가져오기
    raw_data = sheet.get_all_records()
    df = pd.DataFrame(raw_data)
except Exception as e:
    st.error(f"연결 오류: {e}")
    st.stop()

# --- 2. 다우오피스 스타일 UI 레이아웃 ---
st.title("💼 스마트 근태관리 시스템")
now = datetime.now()
today_str = now.strftime("%Y-%m-%d")
time_str = now.strftime("%H:%M:%S")

# 사이드바: 검색 필터
st.sidebar.header("🔍 기록 검색")
search_date = st.sidebar.date_input("날짜 선택", now)
search_name = st.sidebar.text_input("이름 검색")

# 상단 대시보드: 출퇴근 버튼
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    st.info(f"📅 오늘 날짜: {today_str}")
with col2:
    st.info(f"⏰ 현재 시간: {time_str}")

st.divider()

# --- 3. 출퇴근/휴가 입력 기능 ---
st.subheader("🚀 오늘의 근태 기록")
c1, c2, c3, c4 = st.columns(4)

with st.form("attendance_form"):
    user_name = st.text_input("사용자 성함 (시트의 이름과 일치해야 함)")
    action = st.selectbox("활동 선택", ["출근", "퇴근", "휴가 신청"])
    
    submit = st.form_submit_button("기록하기")
    
    if submit:
        if not user_name:
            st.error("성함을 입력해주세요.")
        else:
            # 시트에 데이터 추가 (성함, 날짜, 시간, 상태)
            new_row = [user_name, today_str, 
                       time_str if action == "출근" else "", 
                       time_str if action == "퇴근" else "", 
                       action]
            sheet.append_row(new_row)
            st.success(f"{user_name}님 {action} 처리가 완료되었습니다!")
            st.rerun()

st.divider()

# --- 4. 데이터 조회 (다우오피스 스타일 리스트) ---
st.subheader("📊 근태 기록 리스트")

# 필터링 로직
filtered_df = df.copy()
if search_name:
    filtered_df = filtered_df[filtered_df['성함'].str.contains(search_name)]
# 날짜 형식 맞춰서 필터링
search_date_str = search_date.strftime("%Y-%m-%d")
if '날짜' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['날짜'] == search_date_str]

# 가독성을 높인 테이블 출력
st.dataframe(filtered_df, use_container_width=True)

# 데이터 수정/삭제 안내
st.caption("💡 상세 데이터 수정은 연결된 구글 시트에서 직접 하시면 실시간으로 반영됩니다.")
