from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("signup/", views.UserCreateView.as_view()),
    path("signin/", views.LoginView.as_view()),
    path("signout/", views.LogoutView.as_view()),
    path("password/", views.PasswordChangeView.as_view()),
    path("delete/", views.DeactivateAccountView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("kakao/login/", views.KakaoLogin.as_view(), name="kakao_login"),
    path("kakao/redirect/", views.kakao_redirect, name="kakao_redirect"),
    path("google/login/", views.GoogleLogin.as_view(), name="google_login"),
    # 팔로우
    path("follow/", views.FollowToggleView.as_view()),
    # 대화프로필
    path("chat_profiles/", views.ChatProfileListCreateView.as_view()),
    path("chat_profiles/<int:chatprofile_id>/", views.ChatProfileDetailView.as_view()),
    # 프로필조회
    path("my_profile/", views.MyProfileView.as_view()),
    path("<str:nickname>/", views.UserProfileView.as_view()),
]

# 개발용 미디어 파일 제공 설정
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
