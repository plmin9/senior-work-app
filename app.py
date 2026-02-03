import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import pytz # 한국 시간 설정을 위해 추가
from streamlit_js_eval import get_geolocation

# --- 0. 시간 설정 (한국 표준시) ---
# 서버가 해외에 있어도 한국 시간을 기준으로 작동하게 합니다.
KST = pytz.timezone('Asia/Seoul')

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="스마트경로당지원 근태관리", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F0F4F8; } 
    .main-title { font-size: clamp(1.5rem, 5vw, 2.5rem); font-weight: 900; color: #1B5E20; text-align: center; margin-bottom: 2rem; }
    
    .step-header {
        background-color: #FFFFFF; padding: 12px 18px; border-left: 8px solid #00838F;
        border-radius: 12px; font-size: clamp(1rem, 3vw, 1.4rem); font-weight: 800;
        color: #004D40; margin-top: 20px; margin-bottom: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    .stTabs [data-baseweb="tab-list"] { gap: 10px; padding: 8px; background-color: #CFD8DC; border-radius: 15px; }
    .stTabs [data-baseweb="tab"] { 
        flex: 1; height: clamp(50px, 8vw, 80px); 
        font-size: clamp(0.9rem, 2.5vw, 1.4rem) !important; font-weight: 900 !important; 
        border-radius: 12px !important; background-color: #ECEFF1; color: #455A64; 
    }
    .stTabs [aria-selected="true"] { background-color: #00838F !important; color: white !important; }

    div.stButton > button { 
        border-radius: 20px; height: clamp(4rem, 10vw, 6.5rem) !important; 
        font-size: clamp(1.2rem, 4vw, 1.8rem) !important; font-weight: 900 !important; 
    }
    
    .dashboard-container {
        background: white; padding: 25px; border-radius: 25px; border: 4px solid #00838F;
        display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 15px;
    }
    .stat-item { text-align: center; flex: 1; min-width: 120px; }
    
    .divider { font-size: 2rem; color: #EEE; }
    @media (max-width: 600px) { .divider { display: none; } }

    .map-container { border: 5px solid #004D40; border-radius: 20px; overflow: hidden; }
    .loc-info { background-color: #E0F2F1; padding: 15px; border-radius: 15px; border: 2px solid #00838F; }
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

# --- 3. 유틸리티 함수 ---
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

if 'disp_start' not in st.session_state: st.session_state.disp_start = "-"
if 'disp_end' not in st.session_state: st.session_state.disp_end = "-"
if 'arrived' not in st.session_state: st.session_state.arrived = False

# --- 4. 위치 수집 ---
loc = get_geolocation()

# --- 5. 메인 화면 ---
st.markdown('<div class="main-title">🏢 스마트경로당 통합 관리 시스템</div>', unsafe_allow_html=True)

# 탭 구성
tab_att, tab_vac, tab_admin = st.tabs(["🕒 출퇴근 체크", "🏖️ 내 휴가 확인", "👨‍🏫 관리자 모드"])

# --- [사용자 전용] 출퇴근 탭 ---
with tab_att:
    st.markdown('<div class="step-header">👤 성함 선택</div>', unsafe_allow_html=True)
    cho = st.radio("초성", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True, label_visibility="collapsed")
    all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
    filtered_names = all_names if cho == "전체" else [n for n in all_names if get_chosung(n) == cho]
    selected_user = st.selectbox("성함 선택", ["성함을 선택해 주세요"] + filtered_names, label_visibility="collapsed", key="user_select")

    st.markdown('<div class="step-header">📝 오늘 수행 업무</div>', unsafe_allow_html=True)
    work_options = ["경로당 청소", "배식 및 주방지원", "시설물 안전점검", "사무 업무 보조", "행사 지원", "기타 활동"]
    selected_works = st.multiselect("업무 선택", work_options, placeholder="업무를 골라주세요")
    work_detail = st.text_input("상세 내용", placeholder="상세 내용을 적어주세요")
    combined_work = f"[{', '.join(selected_works)}] {work_detail}".strip()

    is_user_selected = (selected_user != "성함을 선택해 주세요")

    if not is_user_selected:
        st.warning("⚠️ **성함을 먼저 선택**하셔야 버튼이 활성화됩니다.")

    st.markdown(f"""
        <div class="dashboard-container">
            <div class="stat-item">
                <div style="font-size:1rem; color:#666;">☀️ 출근 시각</div>
                <div style="font-size:clamp(2rem, 6vw, 3.5rem); font-weight:900; color:#2E7D32;">{st.session_state.disp_start}</div>
            </div>
            <div class="divider">|</div>
            <div class="stat-item">
                <div style="font-size:1rem; color:#666;">🌙 퇴근 시각</div>
                <div style="font-size:clamp(2rem, 6vw, 3.5rem); font-weight:900; color:#C62828;">{st.session_state.disp_end}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("출근하기", use_container_width=True, disabled=not is_user_selected or st.session_state.arrived or not loc):
            # 💡 한국 시간 적용
            now_kst = datetime.now(KST)
            st.session_state.disp_start = now_kst.strftime("%H:%M:%S")
            st.session_state.arrived = True
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            sheet_attendance.append_row([selected_user, now_kst.strftime("%Y-%m-%d"), st.session_state.disp_start, "", "출근", combined_work, lat, lon])
            st.rerun()
            
    with col_btn2:
        if st.button("퇴근하기", use_container_width=True, disabled=not is_user_selected or not st.session_state.arrived or st.session_state.disp_end != "-"):
            # 💡 한국 시간 적용
            now_kst = datetime.now(KST)
            st.session_state.disp_end = now_kst.strftime("%H:%M:%S")
            try:
                all_records = sheet_attendance.get_all_values()
                today_str = now_kst.strftime("%Y-%m-%d")
                target_row = next((i+1 for i, r in enumerate(all_records) if r[0]==selected_user and r[1]==today_str and r[4]=="출근"), -1)
                if target_row != -1:
                    sheet_attendance.update_cell(target_row, 4, st.session_state.disp_end)
                    sheet_attendance.update_cell(target_row, 5, "퇴근")
                    sheet_attendance.update_cell(target_row, 6, combined_work)
                    st.success("퇴근 확인되었습니다!")
            except: st.error("시트 업데이트 중 오류가 발생했습니다.")
            st.balloons()
            st.rerun()

    st.markdown('<div class="step-header">📍 위치 인증 확인</div>', unsafe_allow_html=True)
    if loc:
        m_col1, m_col2 = st.columns([2, 1])
        with m_col1:
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            df_map = pd.DataFrame([{'latitude': loc['coords']['latitude'], 'longitude': loc['coords']['longitude']}])
            st.map(df_map, zoom=16, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""<div class="loc-info">위도: <b>{loc['coords']['latitude']:.6f}</b><br>경도: <b>{loc['coords']['longitude']:.6f}</b><br><br><small>정상 수신 중</small></div>""", unsafe_allow_html=True)

# --- [사용자 전용] 휴가 탭 ---
with tab_vac:
    if is_user_selected:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        try:
            total = int(pd.to_numeric(u.get('총연차', 0), errors='coerce'))
            used = int(pd.to_numeric(u.get('사용연차', 0), errors='coerce'))
            remain_val = pd.to_numeric(u.get('잔여연차', 0), errors='coerce')
            remain = int(remain_val) if pd.notnull(remain_val) else (total - used)
        except: total, used, remain = 0, 0, 0
        percent = (remain / total) if total > 0 else 0
        st.markdown(f"""<div style="background: white; padding: 30px; border-radius: 25px; border: 3px solid #E0E0E0; text-align: center;"><div style="font-size: 1.8rem; font-weight: 800; color: #1B5E20; margin-bottom: 25px;">🏖️ {selected_user} 어르신 휴가 현황</div><div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px;"><div class="stat-item"><div style="color: #666;">전체 휴가</div><div style="font-size: 2rem; font-weight: 800;">{total}일</div></div><div class="stat-item"><div style="color: #666;">사용한 휴가</div><div style="font-size: 2rem; font-weight: 800; color: #C62828;">{used}일</div></div><div class="stat-item"><div style="color: #666;">남은 휴가</div><div style="font-size: 2rem; font-weight: 800; color: #2E7D32;">{remain}일</div></div></div></div>""", unsafe_allow_html=True)
        st.progress(percent)
    else:
        st.warning("⚠️ 성함을 먼저 선택해 주세요.")

# --- [관리자 전용] 관리자 모드 탭 ---
with tab_admin:
    st.markdown('<div class="step-header">🔒 관리자 인증</div>', unsafe_allow_html=True)
    pw = st.text_input("관리자 비밀번호를 입력하세요", type="password")
    
    if pw == "1234":
        st.success("✅ 인증 성공! 한국 표준시 기준으로 데이터를 불러옵니다.")
        
        adm_tab1, adm_tab2 = st.tabs(["📅 오늘 출근 명단", "📊 전체 연차 현황"])
        
        with adm_tab1:
            # 💡 한국 현재 날짜 기준 필터링
            today_kst = datetime.now(KST).strftime("%Y-%m-%d")
            st.markdown(f"### 📋 오늘({today_kst}) 출근자 명단")
            try:
                all_att = pd.DataFrame(sheet_attendance.get_all_records())
                df_today = all_att[all_att['날짜'] == today_kst]
                if not df_today.empty:
                    st.dataframe(df_today, use_container_width=True)
                else:
                    st.info("아직 오늘 출근한 사람이 없습니다.")
            except: st.error("데이터를 불러오는 데 실패했습니다.")
            
        with adm_tab2:
            st.markdown("### 🏖️ 모든 직원 연차 잔여량")
            st.dataframe(df_vacation, use_container_width=True)
            st.bar_chart(df_vacation.set_index('성함')['잔여연차'])
            
    elif pw != "":
        st.error("비밀번호가 틀렸습니다.")

st.caption("실버 복지 사업단 v6.2 | KST 한국 표준시 적용 완료")
