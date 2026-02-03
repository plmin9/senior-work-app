def get_gspread_client():
    try:
        s = st.secrets["connections"]["gsheets"]
        
        # \n이라는 '글자'를 실제 '줄바꿈'으로 강제로 변환합니다.
        p_key = s["private_key"].replace("\\n", "\n")
        
        creds_info = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": p_key, 
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"연결 설정 실패: {e}")
        return None
