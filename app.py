import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="노인일자리 관리", layout="wide")
st.title("👵 노인일자리 출퇴근 시스템")

try:
    # 1. 커넥션 생성
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 2. 데이터 읽기 (Secrets에 적힌 URL을 명시적으로 사용)
    # worksheet 파라미터를 제거하거나 명확히 하여 첫 번째 시트를 가져옵니다.
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    
    # ttl=0은 캐시를 지우고 새로 읽어오라는 의미입니다.
    df = conn.read(spreadsheet=url, ttl=0)
    
    if df is not None:
        st.success("✅ 데이터를 성공적으로 불러왔습니다!")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ 시트 연결은 성공했으나 데이터가 비어있습니다.")

except Exception as e:
    st.error("❌ 오류 발생")
    st.code(str(e))
    st.info("시트 공유가 '링크가 있는 모든 사용자 - 뷰어'로 되어 있는지 다시 한번 확인 부탁드립니다!")
