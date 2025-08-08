import streamlit as st
import hashlib
import json
import os
from datetime import datetime, timedelta

class AuthSystem:
    def __init__(self):
        self.users_file = "users.json"
        self.load_users()
    
    def load_users(self):
        """사용자 데이터 로드"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # 파일이 손상되었거나 없으면 기본 사용자 생성
                self.users = {
                    "admin": {
                        "password": self.hash_password("admin123"),
                        "role": "admin",
                        "created_at": datetime.now().isoformat(),
                        "last_login": None
                    }
                }
                self.save_users()
        else:
            # 기본 관리자 계정
            self.users = {
                "admin": {
                    "password": self.hash_password("admin123"),
                    "role": "admin",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None
                }
            }
            self.save_users()
    
    def save_users(self):
        """사용자 데이터 저장"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def hash_password(self, password):
        """비밀번호 해시화"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, hashed):
        """비밀번호 검증"""
        return self.hash_password(password) == hashed
    
    def login(self, username, password):
        """로그인 처리"""
        if username in self.users and self.verify_password(password, self.users[username]["password"]):
            # 로그인 성공
            self.users[username]["last_login"] = datetime.now().isoformat()
            self.save_users()
            return True
        return False
    
    def add_user(self, username, password, role="user"):
        """새 사용자 추가 (관리자만)"""
        if username not in self.users:
            self.users[username] = {
                "password": self.hash_password(password),
                "role": role,
                "created_at": datetime.now().isoformat(),
                "last_login": None
            }
            self.save_users()
            return True
        return False
    
    def remove_user(self, username):
        """사용자 삭제 (관리자만)"""
        if username in self.users and username != "admin":
            del self.users[username]
            self.save_users()
            return True
        return False

def init_auth():
    """인증 시스템 초기화"""
    if 'auth_system' not in st.session_state:
        st.session_state.auth_system = AuthSystem()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None

def login_page():
    """로그인 페이지"""
    st.markdown("""
    <div style="text-align: center; padding: 40px;">
        <h1> ArchInsight 로그인</h1>
        <p>AI-driven Project Insight & Workflow</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("사용자명")
        password = st.text_input("비밀번호", type="password")
        submit = st.form_submit_button("로그인", type="primary")
        
        if submit:
            if st.session_state.auth_system.login(username, password):
                st.session_state.authenticated = True
                st.session_state.current_user = username
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("사용자명 또는 비밀번호가 올바르지 않습니다.")
    
    # 관리자 계정 정보 (개발용)
    with st.expander("관리자 계정 정보"):
        st.info("기본 관리자 계정: admin / admin123")

def admin_panel():
    """관리자 패널"""
    if st.session_state.current_user != "admin":
        st.error("관리자 권한이 필요합니다.")
        return
    
    st.markdown("### 👨‍💼 관리자 패널")
    
    # 새 사용자 추가
    with st.expander("새 사용자 추가"):
        with st.form("add_user_form"):
            new_username = st.text_input("새 사용자명")
            new_password = st.text_input("새 비밀번호", type="password")
            new_role = st.selectbox("역할", ["user", "admin"])
            add_submit = st.form_submit_button("사용자 추가")
            
            if add_submit and new_username and new_password:
                if st.session_state.auth_system.add_user(new_username, new_password, new_role):
                    st.success(f"사용자 '{new_username}' 추가 완료!")
                else:
                    st.error("사용자명이 이미 존재합니다.")
    
    # 사용자 목록
    with st.expander("사용자 목록"):
        users_data = []
        for username, user_info in st.session_state.auth_system.users.items():
            users_data.append({
                "사용자명": username,
                "역할": user_info["role"],
                "생성일": user_info["created_at"][:10],
                "마지막 로그인": user_info["last_login"][:10] if user_info["last_login"] else "없음"
            })
        
        if users_data:
            st.dataframe(users_data, use_container_width=True)
        
        # 사용자 삭제
        delete_username = st.text_input("삭제할 사용자명")
        if st.button("사용자 삭제", type="secondary"):
            if st.session_state.auth_system.remove_user(delete_username):
                st.success(f"사용자 '{delete_username}' 삭제 완료!")
                st.rerun()
            else:
                st.error("사용자를 삭제할 수 없습니다.")

def logout():
    """로그아웃"""
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()
