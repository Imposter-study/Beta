from django.urls import path
from .views import ChatAPIView, ChatRegenerateAPIView, RoomAPIView, RoomDetailAPIView

urlpatterns = [
    path("", ChatAPIView.as_view()),
    path("regenerate/", ChatRegenerateAPIView.as_view(), name="chat-regenerate"),
    path("list/", RoomAPIView.as_view()),
    path("<uuid:room_id>/", RoomDetailAPIView.as_view()),
]
