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
    path(
        "chat_profiles/",
        views.ChatProfileView.as_view(),
        name="chat_profile_list_create",
    ),
    path(
        "chat_profiles/<uuid:chatprofile_id>/",
        views.ChatProfileDetailView.as_view(),
        name="chat_profile_detail",
    ),
    path("follow/", views.FollowCreateView.as_view(), name="follow"),
    path("unfollow/<int:to_user_id>/", views.UnfollowView.as_view(), name="unfollow"),
    path(
        "follow/count/<int:user_id>/",
        views.FollowCountView.as_view(),
        name="follow_count",
    ),
    path("<str:nickname>/", views.UserProfileView.as_view()),
]

# 개발용 미디어 파일 제공 설정
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
