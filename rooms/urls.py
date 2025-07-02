# Third-Party Package
from django.urls import path

# Local Apps
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
    path("<uuid:room_uuid>/", RoomDetailAPIView.as_view()),
    # 메시지 관련 기능
    path("<uuid:room_uuid>/messages/", ChatAPIView.as_view()),
    path("<uuid:room_uuid>/messages/<int:chat_id>/", ChatMessageDetailView.as_view()),
    path("<uuid:room_uuid>/suggestions/", ChatSuggestionAPIView.as_view()),
    path("<uuid:room_uuid>/regenerate/", ChatRegenerateAPIView.as_view()),
    # 대화 내역 기능
    path("<uuid:room_uuid>/histories/", HistoryAPIView.as_view()),
    path(
        "<uuid:room_uuid>/histories/<uuid:history_id>/", HistoryDetailAPIView.as_view()
    ),
]
