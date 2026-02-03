import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation
import time

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F7F9FB; } 
    .main-title { font-size: 2rem; font-weight: 900; color: #2E7D32; text-align: center; margin-bottom: 1.5rem; }
    .step-header {
        background-color: #E0F2F1; padding: 8px 15px; border-left: 6px solid #00838F;
        border-radius: 8px; font-size: 1.3rem !important; font-weight: 800 !important;
        color: #004D40; margin-top: 20px; margin-bottom: 10px;
    }
    div.stButton > button { 
        border-radius: 15px; height: 5.5rem !important; font-size: 1.6rem !important; 
        font-weight: 800 !important; background-color: #4CAF50 !important; color: white !important;
    }
    .map-outline-box { border: 4px solid #004D40; border-radius: 15px; overflow: hidden; box-shadow: 0 8px 20px rgba(0,0,0,0.15); }
    </style>
""", unsafe_allow_html=True)

# --- 2. 구글 시트 연결 (기존과 동일) ---
@st.cache_resource
def get_gspread_client():
    try:
        s = st.secrets["connections"]["gsheets"]
        creds_info = {
            "type": "service_account", "project_id": s["project_id"],
            "private_key": s["private_key"].replace("\\n", "\n"),
            "client_email": s["service_account_email"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

client = get_gspread_client()
if client:
    s = st.secrets["connections"]["gsheets"]
    sheet_id = s["spreadsheet"].split("/d/")[1].split("/")[0]
    doc = client.open_by_key(sheet_id)
    sheet_attendance = doc.worksheet("근태기록")
    sheet_vacation = doc.worksheet("연차관리")
    df_vacation = pd.DataFrame(sheet_vacation.get_all_records())
else: st.stop()

# --- 3. 세션 상태 관리 (경로 저장용 추가) ---
if 'disp_start' not in st.session_state: st.session_state.disp_start = "-"
if 'disp_end' not in st.session_state: st.session_state.disp_end = "-"
if 'arrived' not in st.session_state: st.session_state.arrived = False
if 'path_data' not in st.session_state: st.session_state.path_data = [] # 이동 경로 좌표 저장

# --- 4. 유틸리티 함수 ---
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

# --- 5. 메인 화면 ---
st.markdown('<div class="main-title">🏢 스마트경로당지원 근태관리 (경로추적)</div>', unsafe_allow_html=True)

# 초성/성함/업무 선택 (기존 로직 유지)
st.markdown('<div class="step-header">1️⃣ 성함 및 업무 선택</div>', unsafe_allow_html=True)
cho = st.radio("초성", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True, label_visibility="collapsed")
all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered_names = all_names if cho == "전체" else [n for n in all_names if get_chosung(n) == cho]
selected_user = st.selectbox("성함 선택", filtered_names if filtered_names else ["데이터 없음"], label_visibility="collapsed")

work_options = ["경로당 청소", "배식 및 주방지원", "시설물 안전점검", "사무 업무 보조", "행사 지원", "기타 활동"]
selected_works = st.multiselect("업무 선택", work_options, placeholder="업무를 선택해 주세요")
work_detail = st.text_input("상세 업무 입력", placeholder="추가 내용을 입력해 주세요")
combined_work = f"[{', '.join(selected_works)}] {work_detail}".strip()

# --- 6. 실시간 위치 수집 로직 ---
loc = get_geolocation()
if loc and st.session_state.arrived:
    new_point = {'lat': loc['coords']['latitude'], 'lon': loc['coords']['longitude'], 'time': datetime.now().strftime("%H:%M:%S")}
    # 이전 좌표와 다를 경우에만 경로에 추가 (중복 방지)
    if not st.session_state.path_data or (st.session_state.path_data[-1]['lat'] != new_point['lat']):
        st.session_state.path_data.append(new_point)

# --- 7. 근태 관리 탭 ---
tab_attendance, tab_vacation = st.tabs(["🕒 근태관리 & 경로추적", "🏖️ 휴가관리"])

with tab_attendance:
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    
    # 시간 표시 판
    st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 20px; border: 3px solid #00838F; text-align: center; margin-bottom: 25px;">
            <div style="display:flex; justify-content:space-around; align-items:center;">
                <div><div style="font-size:1.1rem; color:#888;">출근 시간</div><div style="font-size:3rem; font-weight:900; color:#2E7D32;">{st.session_state.disp_start}</div></div>
                <div style="font-size:3rem; color:#00838F; font-weight:200;">|</div>
                <div><div style="font-size:1.1rem; color:#888;">퇴근 시간</div><div style="font-size:3rem; font-weight:900; color:#2E7D32;">{st.session_state.disp_end}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 출근하기", use_container_width=True, disabled=st.session_state.arrived or not loc):
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            st.session_state.path_data = [{'lat': lat, 'lon': lon, 'time': st.session_state.disp_start}]
            sheet_attendance.append_row([selected_user, today_date, st.session_state.disp_start, "", "출근", combined_work, lat, lon, ""])
            st.rerun()
            
    with col2:
        if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            try:
                all_records = sheet_attendance.get_all_values()
                target_row = -1
                for idx, row in enumerate(all_records):
                    if row[0] == selected_user and row[1] == today_date and row[4] == "출근":
                        target_row = idx + 1
                
                if target_row != -1:
                    # 이동 경로 정보를 텍스트로 변환 (예: 12:00(37.1, 127.1) -> 12:05(37.2, 127.2))
                    path_str = " > ".join([f"{p['time']}({p['lat']:.4f},{p['lon']:.4f})" for p in st.session_state.path_data])
                    
                    sheet_attendance.update_cell(target_row, 4, st.session_state.disp_end)
                    sheet_attendance.update_cell(target_row, 5, "퇴근")
                    sheet_attendance.update_cell(target_row, 6, combined_work)
                    # 9번째 열(I열)에 전체 이동 경로 저장 (시트에 '이동경로' 컬럼 추가 필요)
                    sheet_attendance.update_cell(target_row, 9, path_str)
                    st.success("퇴근 및 이동 경로가 저장되었습니다!")
                else: st.error("기록을 찾을 수 없습니다.")
            except Exception as e: st.error(f"오류: {e}")
            st.balloons()
            st.rerun()

    # --- 8. 이동 경로 시각화 ---
    st.markdown('<div class="step-header">📍 실시간 이동 경로 확인</div>', unsafe_allow_html=True)
    if loc:
        m1, m2 = st.columns([1.5, 1])
        with m1:
            st.markdown('<div class="map-outline-box">', unsafe_allow_html=True)
            if st.session_state.path_data:
                df_path = pd.DataFrame(st.session_state.path_data)
                # 지도에 이동 경로 표시 (st.map은 점을 찍어주며, 여러 점이 찍히면 경로가 됨)
                st.map(df_path, zoom=14, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with m2:
            st.write("**👣 실시간 위치 로그 (최근 5개)**")
            for p in reversed(st.session_state.path_data[-5:]):
                st.write(f"⏱️ {p['time']} | 위도: `{p['lat']:.5f}` | 경도: `{p['lon']:.5f}`")
            if st.session_state.arrived:
                st.info("💡 앱을 켜두시면 이동 경로가 자동으로 기록됩니다.")
    else:
        st.warning("위치 정보를 수신 중입니다...")

with tab_vacation:
    # (연차 관리 코드 동일)
    st.markdown('<div class="step-header">🏖️ 나의 휴가 현황</div>', unsafe_allow_html=True)
    if not df_vacation.empty and selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        st.success(f"🌟 {selected_user}님, 남은 휴가는 **{u.get('잔여연차', 0)}일**입니다.")

st.caption("실버 복지 사업단 v4.7 | 실시간 경로 추적 시스템")
