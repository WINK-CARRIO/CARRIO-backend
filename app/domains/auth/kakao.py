import requests
from app.config import settings

# 카카오에 access_token 요청
def get_kakao_access_token(code: str) -> str:
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_CLIENT_ID,
        "client_secret": settings.KAKAO_CLIENT_SECRET, #비즈니스앱이면 secret 키도 무조건 필요함
        "redirect_uri": settings.KAKAO_REDIRECT_URI,
        "code": code,
    }

    try:
        res = requests.post(url, data=data)
        res.raise_for_status()
    except requests.HTTPError as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="카카오 토큰 발급에 실패했습니다. 앱 권한 설정을 확인하세요."
        )

    return res.json()["access_token"]


# access_token으로 카카오 유저 정보 조회
def get_kakao_user(code: str) -> dict:
    access_token = get_kakao_access_token(code)

    url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    res = requests.get(url, headers=headers)
    res.raise_for_status()

    data = res.json()
    return {
        "oauth_id": str(data["id"]),
        "email": data["kakao_account"].get("email"),
        "name": data["properties"].get("nickname"),
    }