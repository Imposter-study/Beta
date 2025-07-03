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
    path("google/login/", views.GoogleLogin.as_view(), name="google_login"),
    
    # 대화 프로필 관련
    path(
        "chat_profiles/",
        views.ChatProfileView.as_view(),
        name="chat_profile_list_create",
    ),
    path(
        "chat_profiles/<uuid:chatprofile_uuid>/",
        views.ChatProfileDetailView.as_view(),
        name="chat_profile_detail",
    ),

    # 팔로우 관련
    path("follow/", views.FollowCreateView.as_view(), name="follow"),
    path("unfollow/<uuid:to_user_id>/", views.UnfollowView.as_view(), name="unfollow"),
    path(
        "follow/count/<uuid:user_id>/",
        views.FollowCountView.as_view(),
        name="follow_count",
    ),

    # 마이페이지 전용 URL (조회, 수정)
    path("my_profile/", views.MyProfileAPIView.as_view(), name="my_profile"),
    path(
        "creators/<uuid:user_id>/profile/",
        views.UserPublicProfileView.as_view(),
        name="user_profile",
    ),
]

# 개발용 미디어 파일 제공 설정
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
