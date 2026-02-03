import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 페이지 설정 ---
st.set_page_config(page_title="노인일자리 스마트 근태관리", layout="wide")

# --- CSS 디자인 ---
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .business-unit { font-size: 22px; color: #4B5563; margin-bottom: 25px; }
    .status-box { background-color: #F8FAFC; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .time-text { font-size: 28px; font-weight: bold; color: #2563EB; }
    .stat-label { font-size: 16px; color: #64748B; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)    

# --- 구글 시트 연결 함수 ---
@st.cache_resource
def get_gspread_client():
    s = st.secrets["connections"]["gsheets"]
    creds_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key": s["private_key"].replace("\\n", "\n"),
        "client_email": s["service_account_email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

try:
    client = get_gspread_client()
    s = st.secrets["connections"]["gsheets"]
    sheet_id = s["spreadsheet"].split("/d/")[1].split("/")[0]
    doc = client.open_by_key(sheet_id)
    
    # 각 시트 탭 연결
    sheet_attendance = doc.worksheet("근태기록")
    sheet_vacation = doc.worksheet("연차관리")
    sheet_notice = doc.worksheet("공지사항")
    
    # 데이터 불러오기
    df_vacation = pd.DataFrame(sheet_vacation.get_all_records())
    df_notice = pd.DataFrame(sheet_notice.get_all_records())
except Exception as e:
    st.error(f"시트 연결 중 오류가 발생했습니다: {e}")
    st.stop()

# --- 상단 헤더 ---
st.markdown('<div class="main-title">📊 근태현황</div>', unsafe_allow_html=True)
st.markdown('<div class="business-unit">🏢 실버 복지 사업단</div>', unsafe_allow_html=True)

now = datetime.now()
st.info(f"📅 **현재 정보:** {now.strftime('%Y년 %m월 %d일 %H:%M:%S')}")

# --- 사용자 선택 (로그인 대용) ---
user_list = df_vacation['성함'].tolist() if not df_vacation.empty else ["등록된 사용자 없음"]
selected_user = st.selectbox("👤 본인의 성함을 선택하세요", user_list)

# --- GPS 및 지도 섹션 ---
st.subheader("📍 위치 인증 및 출퇴근")
loc = get_geolocation()
col_map, col_btns = st.columns([2, 1])

with col_map:
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
    else:
        st.warning("위치 권한을 허용하면 지도가 나타납니다.")

# 출퇴근 상태 관리 (임시 세션)
if 'arrived' not in st.session_state: st.session_state.arrived = False
if 'start_time' not in st.session_state: st.session_state.start_time = "--:--"

with col_btns:
    st.markdown(f'<div class="status-box"><span class="stat-label">출근 시간</span><br><span class="time-text">{st.session_state.start_time}</span></div>', unsafe_allow_html=True)
    st.write("")
    
    work_mode = st.selectbox("📝 업무 내용 선택", ["행정지원", "현장관리", "상담업무", "기타"])
    
    # 출근 버튼
    if st.button("🚀 출근하기", use_container_width=True, disabled=st.session_state.arrived or not loc):
        st.session_state.arrived = True
        st.session_state.start_time = datetime.now().strftime("%H:%M")
        sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.start_time, "", "출근", work_mode, lat, lon])
        st.success("출근 기록 완료!")
        st.rerun()

    # 퇴근 버튼
    if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived):
        end_time = datetime.now().strftime("%H:%M")
        # 해당 날짜/이름의 행을 찾아 퇴근시간 업데이트 (간략화를 위해 추가행 입력)
        sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), "", end_time, "퇴근", work_mode, "", ""])
        st.session_state.arrived = False
        st.session_state.start_time = "--:--"
        st.success("퇴근 처리되었습니다. 수고하셨습니다!")
        st.rerun()

st.divider()

# --- 연차 현황 섹션 ---
st.subheader("🏖️ 연차 및 근로 정보")
if not df_vacation.empty and selected_user in df_vacation['성함'].values:
    user_data = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
    v_total, v_used, v_remain = user_data['총연차'], user_data['사용연차'], user_data['잔여연차']
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="status-box"><span class="stat-label">총 연차</span><br><b>{v_total}일</b></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="status-box"><span class="stat-label">사용 연차</span><br><b>{v_used}일</b></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="status-box"><span class="stat-label">잔여 연차</span><br><b>{v_remain}일</b></div>', unsafe_allow_html=True)
    
    st.write("📊 **연차 사용 현황**")
    st.progress(float(v_used / v_total) if v_total > 0 else 0.0)
    st.info(f"⏱️ 소정근로시간: {user_data.get('소정근로시간', 0)}시간")

# 연차 신청 팝업
if st.button("➕ 연차 신청하기"):
    @st.dialog("연차/휴가 신청서")
    def vacation_form():
        d = st.date_input("휴가 날짜")
        t = st.selectbox("유형", ["연차", "오전반차", "오후반차", "경조사"])
        reason = st.text_input("사유")
        if st.button("제출하기"):
            sheet_attendance.append_row([selected_user, d.strftime("%Y-%m-%d"), "", "", t, reason])
            st.success("신청 완료!")
            st.rerun()
    vacation_form()

st.divider()

# --- 알림 및 검색 섹션 ---
col_search, col_notice = st.columns([2, 1])

with col_search:
    st.subheader("🔍 기록 조회")
    tab_week, tab_month = st.tabs(["주간", "월간"])
    with tab_week:
        st.write("최근 7일간의 기록입니다.")
        # 실제 구현 시 sheet_attendance에서 filter하여 표시
        
with col_notice:
    st.subheader("🔔 공지사항")
    for idx, row in df_notice.iterrows():
        with st.expander(f"{row['날짜']} | {row['제목']}"):
            st.write(row['세부내용'])
