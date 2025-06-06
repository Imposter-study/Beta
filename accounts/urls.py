from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.UserCreateView.as_view()),
    path("<str:nickname>/", views.UserProfileView.as_view()),
]
