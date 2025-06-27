from django.urls import path
from .views import ChatAPIView, ChatRegenerateAPIView, RoomAPIView, RoomDetailAPIView

urlpatterns = [
    path("", RoomAPIView.as_view()),
    path("chat/", ChatAPIView.as_view()),
    path("regenerate/", ChatRegenerateAPIView.as_view(), name="chat-regenerate"),
    path("<uuid:room_id>/", RoomDetailAPIView.as_view()),
]
