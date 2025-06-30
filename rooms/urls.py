from django.urls import path
from .views import (
    RoomAPIView,
    RoomDetailAPIView,
    ChatAPIView,
    ChatMessageDetailView,
    ChatSuggestionAPIView,
    ChatRegenerateAPIView,
    HistoryAPIView,
    HistoryDetailAPIView,
)

urlpatterns = [
    # 채팅방 관련 기능
    path("", RoomAPIView.as_view()),
    path("<uuid:room_id>/", RoomDetailAPIView.as_view()),
    # 메시지 관련 기능
    path("<uuid:room_id>/messages/", ChatAPIView.as_view()),
    path("<uuid:room_id>/messages/<int:chat_id>/", ChatMessageDetailView.as_view()),
    path("<uuid:room_id>/suggestions/", ChatSuggestionAPIView.as_view()),
    path("<uuid:room_id>/regenerate/", ChatRegenerateAPIView.as_view()),
    # 대화 내역 기능
    path("<uuid:room_id>/histories/", HistoryAPIView.as_view()),
    path("<uuid:room_id>/histories/<uuid:history_id>/", HistoryDetailAPIView.as_view()),
]
