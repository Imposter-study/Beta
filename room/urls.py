from django.urls import path
from . import views


urlpatterns = [
    path("", views.ChatRoomView.as_view()),
]
