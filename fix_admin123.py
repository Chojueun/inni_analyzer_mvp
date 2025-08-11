import bcrypt
import json
from datetime import datetime

def fix_admin123_password():
    """admin 패스워드를 admin123으로 변경"""
    
    # admin123 패스워드 설정
    admin_password = "admin123"
    
    # bcrypt로 해시 생성
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), salt)
    
    # 새로운 사용자 데이터
    users_data = {
        "admin": {
            "password": hashed_password.decode('utf-8'),
            "role": "admin",
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
    }
    
    # 파일 저장
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)
    
    print("✅ users.json 파일이 admin123 패스워드로 수정되었습니다!")
    print(f"Admin 사용자명: admin")
    print(f"Admin 패스워드: {admin_password}")
    print(f"해시된 패스워드: {hashed_password.decode('utf-8')}")

if __name__ == "__main__":
    fix_admin123_password()
