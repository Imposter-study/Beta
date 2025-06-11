from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("signup/", views.UserCreateView.as_view()),
    path("signin/", views.LoginView.as_view()),
    path("signout/", views.LogoutView.as_view()),
    path("password/", views.PasswordChangeView.as_view()),
    path("delete/", views.DeactivateAccountView.as_view()),
    path("auth-check/", views.AuthCheckView.as_view(), name="auth-check"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("<str:nickname>/", views.UserProfileView.as_view()),
]
