from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register("", views.UserViewSet, basename="user")

urlpatterns = [
    path("signin/", views.LoginView.as_view()),
    path("signout/", views.LogoutView.as_view()),
    path("password/", views.PasswordChangeView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("kakao/login/", views.KakaoLogin.as_view(), name="kakao_login"),
    path("kakao/redirect/", views.kakao_redirect, name="kakao_redirect"),
    path("google/login/", views.GoogleLogin.as_view(), name="google_login"),
    path(
        "social/signup/add_info/",
        views.SocialSignupAddInfoView.as_view(),
        name="social_signup_add_info",
    ),
    # 팔로우
    path("follow/", views.FollowToggleView.as_view()),
    # 대화프로필
    path("chat_profiles/", views.ChatProfileListCreateView.as_view()),
    path(
        "chat_profiles/<uuid:chatprofile_uuid>/", views.ChatProfileDetailView.as_view()
    ),
]

# 개발용 미디어 파일 제공 설정
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# UserViewSet 회원 관련 url (회원가입, 회원탈퇴, 회원정보 수정, 회원정보 조회)
urlpatterns += router.urls