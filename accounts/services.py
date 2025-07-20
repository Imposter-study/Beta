from rest_framework_simplejwt.tokens import RefreshToken

def generate_jwt_tokens(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)

def build_social_login_response(user, social_account, provider):
    access_token, refresh_token = generate_jwt_tokens(user)
    is_signup = user.gender != "O" and bool(user.birth_date)
    base_response = {
        "is_signup": is_signup,
        "uuid": user.uuid,
        "access": access_token,
        "refresh": refresh_token,
    }
    if provider == "kakao":
        base_response["kakao_id"] = social_account.uid
    elif provider == "google":
        base_response["google_id"] = social_account.uid
    return base_response, is_signup