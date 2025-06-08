from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.UserCreateView.as_view()),
    path('signin/', views.LoginView.as_view()),
    path('signout/', views.LogoutView.as_view()),
    path('password/', views.PasswordChangeView.as_view()),
    path('delete/', views.DeactivateAccountView.as_view()),
    path("<str:nickname>/", views.UserProfileView.as_view()),
]
