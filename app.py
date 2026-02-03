import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F7F9FB; } 
    .main-title { font-size: 2.2rem; font-weight: 900; color: #1B5E20; text-align: center; margin-bottom: 1.5rem; }
    .step-header {
        background-color: #E0F2F1; padding: 12px 20px; border-left: 8px solid #00838F;
        border-radius: 10px; font-size: 1.5rem !important; font-weight: 800 !important;
        color: #004D40; margin-top: 25px; margin-bottom: 15px;
    }
    /* 지도 영역 강조 */
    .map-container { border: 5px solid #004D40; border-radius: 20px; overflow: hidden; margin-top: 10px; }
    
    div.stButton > button { 
        border-radius: 20px; height: 6rem !important; font-size: 1.8rem !important; 
        font-weight: 900 !important; background-color: #4CAF50 !important; color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 구글 시트 연결 ---
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

# --- 3. 유틸리티 및 세션 관리 ---
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

if 'disp_start' not in st.session_state: st.session_state.disp_start = "-"
if 'disp_end' not in st.session_state: st.session_state.disp_end = "-"
if 'arrived' not in st.session_state: st.session_state.arrived = False
if 'path_history' not in st.session_state: st.session_state.path_history = []

# --- 4. 위치 정보 수집 (가장 먼저 실행) ---
loc = get_geolocation()

# --- 5. 메인 화면 ---
st.markdown('<div class="main-title">🏢 스마트경로당지원 근태관리</div>', unsafe_allow_html=True)

st.markdown('<div class="step-header">1️⃣ 이름 첫글자(초성) 선택</div>', unsafe_allow_html=True)
cho = st.radio("초성", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True, label_visibility="collapsed")

st.markdown('<div class="step-header">2️⃣ 본인 성함 선택</div>', unsafe_allow_html=True)
all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered_names = all_names if cho == "전체" else [n for n in all_names if get_chosung(n) == cho]
selected_user = st.selectbox("성함 선택", filtered_names if filtered_names else ["데이터 없음"], label_visibility="collapsed")

st.markdown('<div class="step-header">3️⃣ 오늘 하시는 업무 (여러개 가능)</div>', unsafe_allow_html=True)
work_options = ["경로당 청소", "배식 및 주방지원", "시설물 안전점검", "사무 업무 보조", "행사 지원", "기타 활동"]
selected_works = st.multiselect("업무 선택", work_options, placeholder="업무를 선택해 주세요")
work_detail = st.text_input("상세 내용 (직접 쓰기)", placeholder="기타 상세 내용을 적어주세요")
combined_work = f"[{', '.join(selected_works)}] {work_detail}".strip()

# --- 6. 실시간 경로 누적 ---
if loc and st.session_state.arrived:
    current_pos = {'latitude': loc['coords']['latitude'], 'longitude': loc['coords']['longitude'], 'time': datetime.now().strftime("%H:%M")}
    if not st.session_state.path_history or st.session_state.path_history[-1]['latitude'] != current_pos['latitude']:
        st.session_state.path_history.append(current_pos)

# --- 7. 탭 구성 ---
tab_attendance, tab_vacation = st.tabs(["🕒 근태관리", "🏖️ 휴가관리"])

with tab_attendance:
    st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 25px; border: 4px solid #00838F; text-align: center; margin-bottom: 25px;">
            <div style="display:flex; justify-content:space-around; align-items:center;">
                <div><div style="font-size:1.2rem; color:#666;">출근 시간</div><div style="font-size:3.5rem; font-weight:900; color:#2E7D32;">{st.session_state.disp_start}</div></div>
                <div style="font-size:3.5rem; color:#CCC;">|</div>
                <div><div style="font-size:1.2rem; color:#666;">퇴근 시간</div><div style="font-size:3.5rem; font-weight:900; color:#C62828;">{st.session_state.disp_end}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 출근하기", use_container_width=True, disabled=st.session_state.arrived or not loc):
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            st.session_state.path_history = [{'latitude': lat, 'longitude': lon, 'time': datetime.now().strftime("%H:%M")}]
            sheet_attendance.append_row([selected_user, datetime.now().strftime("%Y-%m-%d"), st.session_state.disp_start, "", "출근", combined_work, lat, lon])
            st.rerun()
            
    with col2:
        if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            # (중략: 시트 업데이트 로직 기존과 동일)
            st.balloons()
            st.rerun()

    # --- 🗺️ 지도 복구 섹션 ---
    st.markdown('<div class="step-header">📍 현재 위치 및 이동 경로</div>', unsafe_allow_html=True)
    
    if loc:
        m1, m2 = st.columns([1.5, 1])
        with m1:
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            # 지도 데이터 준비 (latitude, longitude 컬럼명 명시)
            if st.session_state.path_history:
                df_map = pd.DataFrame(st.session_state.path_history)
            else:
                df_map = pd.DataFrame([{'latitude': loc['coords']['latitude'], 'longitude': loc['coords']['longitude']}])
            
            # st.map 실행
            st.map(df_map, zoom=15, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with m2:
            st.info(f"🚩 **위치 인증 완료**\n\n위도: `{loc['coords']['latitude']:.6f}`\n\n경도: `{loc['coords']['longitude']:.6f}`")
            if st.session_state.path_history:
                st.write("**👣 최근 이동 기록**")
                for p in reversed(st.session_state.path_history[-3:]):
                    st.write(f"- {p['time']} 위치 확인")
    else:
        st.error("⚠️ 지도를 표시할 수 없습니다. 스마트폰의 **GPS(위치)**를 켜고, 브라우저의 **위치 권한**을 허용해 주세요.")

with tab_vacation:
    st.markdown('<div class="step-header">🏖️ 나의 휴가 현황</div>', unsafe_allow_html=True)
    # (연차 코드 동일)
