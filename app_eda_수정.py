import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home - 지역별 인구 분석 앱")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
        ---
        **📊 지역별 인구 추이 분석 (Population Trends)**  
        - 파일명: `population_trends.csv`  
        - 주요 변수:
          - `연도` (Year)
          - `지역` (Region)
          - `인구`, `출생아수(명)`, `사망자수(명)` 등  
        - 분석 목표:
          - 연도별 전체 인구 변화
          - 지역별 인구 증가/감소 순위
          - 증감률 계산
          - 다양한 시각화를 통한 인사이트 도출
        """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 인구 통계 EDA")
        uploaded = st.file_uploader("population_trends.csv 업로드", type="csv")
        if not uploaded:
            st.info("CSV 파일을 업로드해주세요.")
            return

        # 데이터 로드 및 전처리
        df = pd.read_csv(uploaded)
        df = df.replace('-', 0)
        cols_to_convert = ['인구', '출생아수(명)', '사망자수(명)']
        df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric)

        tabs = st.tabs([
            "기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"
        ])

        # 1. 기초 통계
        with tabs[0]:
            st.header("📌 기초 통계")
            st.subheader("데이터프레임 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("기초 통계량 (`df.describe()`)")
            st.dataframe(df.describe())

        # 2. 연도별 전체 인구 추이
        with tabs[1]:
            st.header("📈 연도별 전체 인구 추이")
            df_total = df[df['지역'] == '전국']
            fig, ax = plt.subplots()
            sns.lineplot(x='연도', y='인구', data=df_total, ax=ax)
            ax.set_title("Total Population by Year")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)

            st.markdown("**2035년 인구 예측 (최근 3년 추세 기반)**")
            recent = df_total.sort_values(by='연도', ascending=False).head(3)
            slope = (recent.iloc[0]['인구'] - recent.iloc[2]['인구']) / 2
            year_gap = 2035 - recent.iloc[0]['연도']
            pred_2035 = recent.iloc[0]['인구'] + slope * year_gap
            st.write(f"2035년 예측 인구: **{int(pred_2035):,}명**")

        # 3. 지역별 인구 변화량
        with tabs[2]:
            st.header("🏙️ Population Change by Region (Last 5 Years)")
            year_range = sorted(df['연도'].unique())[-5:]
            df_recent = df[df['연도'].isin(year_range) & (df['지역'] != '전국')]

            # Translate region names to English
            region_translation = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            df_recent['지역'] = df_recent['지역'].map(region_translation)

            # Pivot table for population changes
            df_pivot = df_recent.pivot(index='지역', columns='연도', values='인구')
            df_pivot['Change'] = df_pivot[year_range[-1]] - df_pivot[year_range[0]]
            df_pivot['Change Rate'] = (df_pivot['Change'] / df_pivot[year_range[0]]) * 100

            # Chart 1: Population Change (in people)
            fig1, ax1 = plt.subplots()
            sns.barplot(x='Change', y=df_pivot.index, data=df_pivot.reset_index(), ax=ax1)
            ax1.set_xlabel("Population Change (People)")
            ax1.set_ylabel("Region")
            st.pyplot(fig1)

            # Chart 2: Population Change Rate (%)
            fig2, ax2 = plt.subplots()
            sns.barplot(x='Change Rate', y=df_pivot.index, data=df_pivot.reset_index(), ax=ax2)
            ax2.set_xlabel("Population Change Rate (%)")
            ax2.set_ylabel("Region")
            st.pyplot(fig2)


        # 4. 증감률 상위 지역/연도
        with tabs[3]:
            st.header("🔍 증감률 상위 지역/연도")
            df_temp = df[df['지역'] != '전국'].copy()
            df_temp.sort_values(by=['지역', '연도'], inplace=True)
            df_temp['증감'] = df_temp.groupby('지역')['인구'].diff()
            top = df_temp.sort_values(by='증감', ascending=False).head(100)
            top['증감'] = top['증감'].astype(int)
            st.dataframe(
                top.style.background_gradient(subset='증감', cmap='bwr').format({'증감': "{:,}"})
            )

        # 5. 시각화
        with tabs[4]:
            st.header("📊 누적 영역 그래프 (지역별 인구)")
            df_area = df[df['지역'] != '전국'].pivot(index='연도', columns='지역', values='인구')
            fig, ax = plt.subplots(figsize=(10, 6))
            df_area.plot.area(ax=ax)
            ax.set_title("Population by Region (Area Chart)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
