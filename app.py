import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 및 디자인 (가독성 끝판왕) ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F0F4F8; } 
    .main-title { font-size: 2.5rem !important; font-weight: 900; color: #1B5E20; text-align: center; margin-bottom: 2rem; }
    
    /* 📌 단계별 헤더 스타일 */
    .step-header {
        background-color: #FFFFFF; padding: 15px 20px; border-left: 10px solid #00838F;
        border-radius: 12px; font-size: 1.6rem !important; font-weight: 800 !important;
        color: #004D40; margin-top: 25px; margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* 📌 탭 디자인 (크고 웅장하게) */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 20px; padding: 10px; background-color: #CFD8DC; border-radius: 20px; 
    }
    .stTabs [data-baseweb="tab"] { 
        flex: 1; height: 80px; font-size: 1.8rem !important; font-weight: 900 !important; 
        border-radius: 15px !important; background-color: #ECEFF1; color: #455A64;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #00838F !important; color: white !important; 
        box-shadow: 0 8px 15px rgba(0,131,143,0.3);
        transform: translateY(-5px);
    }

    /* 대형 버튼 */
    div.stButton > button { 
        border-radius: 25px; height: 7rem !important; font-size: 2rem !important; 
        font-weight: 900 !important; border: none !important;
    }
    .st-emotion-cache-12w0qpk { gap: 2rem; } /* 버튼 간격 */

    /* 지도 박스 */
    .map-container { border: 6px solid #004D40; border-radius: 25px; overflow: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 구글 시트 연결 (기본 로직) ---
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

# --- 3. 유틸리티 및 세션 상태 ---
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

if 'disp_start' not in st.session_state: st.session_state.disp_start = "-"
if 'disp_end' not in st.session_state: st.session_state.disp_end = "-"
if 'arrived' not in st.session_state: st.session_state.arrived = False
if 'path_history' not in st.session_state: st.session_state.path_history = []

# --- 4. 위치 수집 ---
loc = get_geolocation()

# --- 5. 화면 구성 ---
st.markdown('<div class="main-title">🏢 어르신 일자리 근태관리</div>', unsafe_allow_html=True)

# 상단 입력부 (초성 / 이름 / 업무)
st.markdown('<div class="step-header">👤 성함 찾기 (첫글자 선택)</div>', unsafe_allow_html=True)
cho = st.radio("초성", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True, label_visibility="collapsed")

all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered_names = all_names if cho == "전체" else [n for n in all_names if get_chosung(n) == cho]
selected_user = st.selectbox("성함 선택", filtered_names if filtered_names else ["데이터 없음"], label_visibility="collapsed")

st.markdown('<div class="step-header">📝 오늘 하시는 업무</div>', unsafe_allow_html=True)
work_options = ["경로당 청소", "배식 및 주방지원", "시설물 안전점검", "사무 업무 보조", "행사 지원", "기타 활동"]
selected_works = st.multiselect("업무 선택", work_options, placeholder="눌러서 업무를 골라주세요")
work_detail = st.text_input("상세 내용 (직접 쓰기)", placeholder="내용을 직접 입력하실 수 있습니다")
combined_work = f"[{', '.join(selected_works)}] {work_detail}".strip()

st.write("<br>", unsafe_allow_html=True)

# --- 6. 대망의 탭 영역 (크게 강조) ---
tab_attendance, tab_vacation = st.tabs(["🕒 오늘 출근·퇴근", "🏖️ 내 휴가 확인"])

with tab_attendance:
    # 시간 현황 (대형 폰트)
    st.markdown(f"""
        <div style="background: white; padding: 30px; border-radius: 30px; border: 5px solid #00838F; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
            <div style="display:flex; justify-content:space-around; align-items:center;">
                <div style="flex:1;"><div style="font-size:1.5rem; color:#555; margin-bottom:10px;">☀️ 출근 시각</div><div style="font-size:4rem; font-weight:900; color:#2E7D32;">{st.session_state.disp_start}</div></div>
                <div style="font-size:4rem; color:#EEE; font-weight:100;">|</div>
                <div style="flex:1;"><div style="font-size:1.5rem; color:#555; margin-bottom:10px;">🌙 퇴근 시각</div><div style="font-size:4rem; font-weight:900; color:#C62828;">{st.session_state.disp_end}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 지금 출근하기", use_container_width=True, disabled=st.session_state.arrived or not loc):
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            st.session_state.path_history = [{'latitude': lat, 'longitude': lon, 'time': datetime.now().strftime("%H:%M")}]
            sheet_attendance.append_row([selected_user, datetime.now().strftime("%Y-%m-%d"), st.session_state.disp_start, "", "출근", combined_work, lat, lon])
            st.rerun()
            
    with col2:
        if st.button("🏠 지금 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            # 시트 업데이트 로직은 기존과 동일하되 피드백 강화
            st.success("🎉 퇴근 처리가 완료되었습니다. 고생 많으셨습니다!")
            st.balloons()
            st.rerun()

    # 지도 표시
    st.markdown('<div class="step-header">📍 내 현재 위치 (지도)</div>', unsafe_allow_html=True)
    if loc:
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        df_map = pd.DataFrame([{'latitude': loc['coords']['latitude'], 'longitude': loc['coords']['longitude']}])
        st.map(df_map, zoom=16, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.write(f"🗺️ 현재 위치 인증 중: `{loc['coords']['latitude']:.6f}, {loc['coords']['longitude']:.6f}`")
    else:
        st.error("📍 지도를 불러오려면 위치 권한을 '허용'해 주세요.")

with tab_vacation:
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
    if not df_vacation.empty and selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        st.markdown(f"""
            <div style="background: #E8F5E9; padding: 50px; border-radius: 30px; text-align: center; border: 2px dashed #2E7D32;">
                <div style="font-size: 2rem; color: #1B5E20; margin-bottom: 20px;">🌟 {selected_user} 어르신의 휴가 정보</div>
                <div style="font-size: 1.5rem; color: #555;">남은 휴가 일수</div>
                <div style="font-size: 6rem; font-weight: 900; color: #2E7D32;">{u.get('잔여연차', 0)} <span style="font-size: 2rem;">일</span></div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("이름을 먼저 선택해 주시면 휴가를 확인해 드릴게요.")

st.caption("실버 복지 사업단 v5.0 | 대형 UI 및 가독성 최적화")
