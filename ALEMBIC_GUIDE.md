# 🗄️ Alembic 마이그레이션 가이드

이 프로젝트는 **Alembic**을 사용하여 데이터베이스 스키마를 버전 관리합니다.

---

## 📖 Alembic이란?

- 데이터베이스의 "Git" 같은 도구
- 테이블 구조 변경 사항을 파일로 저장하고 팀원들과 공유
- 변경 이력 관리 및 롤백 가능

---

## 🚀 팀원 초기 설정 (최초 1회만)

프로젝트를 클론받은 후:

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. Docker로 PostgreSQL 실행
docker-compose up -d

# 3. DB 스키마 동기화 (테이블 자동 생성)
alembic upgrade head

# 4. 서버 실행
python3 -m uvicorn app.main:app --reload
```

**이것만 하면 끝!** ✅

---

## 🔄 개발 중 워크플로우

### 1️⃣ 다른 팀원이 DB 구조를 변경했을 때

```bash
# Git에서 최신 코드 받기
git pull

# DB 스키마 동기화
alembic upgrade head
```

### 2️⃣ 내가 DB 구조를 변경할 때

**예시: User 모델에 `phone` 필드 추가**

```python
# app/domains/users/models.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255))
    phone = Column(String(20))  # ← 새로 추가!
```

**마이그레이션 생성 및 적용:**

```bash
# 1. 마이그레이션 파일 자동 생성
alembic revision --autogenerate -m "Add phone field to users"

# 2. DB에 적용
alembic upgrade head

# 3. Git 커밋
git add alembic/versions/*.py
git commit -m "Add phone field to users table"
git push
```

---

## 📝 자주 사용하는 명령어

| 명령어 | 설명 |
|--------|------|
| `alembic upgrade head` | 최신 마이그레이션 적용 |
| `alembic revision --autogenerate -m "메시지"` | 마이그레이션 자동 생성 |
| `alembic downgrade -1` | 이전 버전으로 롤백 |
| `alembic current` | 현재 마이그레이션 버전 확인 |
| `alembic history` | 마이그레이션 이력 보기 |

---

## ⚠️ 주의사항

### 1. `Base.metadata.create_all()` 사용 금지

```python
# ❌ 이제 사용하지 않음
Base.metadata.create_all(bind=engine)

# ✅ 대신 Alembic 사용
# alembic upgrade head
```

### 2. 마이그레이션 파일은 Git에 커밋

```bash
# alembic/versions/*.py 파일은 꼭 커밋!
git add alembic/versions/
git commit -m "Add migration"
```

### 3. 충돌 발생 시

여러 팀원이 동시에 마이그레이션을 만들면 충돌 가능:

```bash
# 최신 마이그레이션 받기
git pull

# 내 마이그레이션 다시 생성
rm alembic/versions/내파일.py
alembic revision --autogenerate -m "내 변경사항"
alembic upgrade head
```

---

## 🐛 문제 해결

### DB 연결 안 될 때

```bash
# Docker 컨테이너 재시작
docker-compose down -v
docker-compose up -d

# DB 스키마 다시 적용
alembic upgrade head
```

### 마이그레이션 꼬였을 때 (최후의 수단)

```bash
# ⚠️ 주의: DB 데이터가 모두 삭제됩니다!
docker-compose down -v
docker-compose up -d
alembic upgrade head
```

---

## 📚 더 자세한 정보

- [Alembic 공식 문서](https://alembic.sqlalchemy.org/)
- 팀 내 질문: Slack #backend 채널
