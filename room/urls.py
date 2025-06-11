from django.urls import path
from .views import ChatRoomView, RoomListView, RoomDetailView

urlpatterns = [
    # 채팅 메시지 전송
    path("", ChatRoomView.as_view(), name="chat-room"),
    # 채팅방 목록 조회
    path("list/", RoomListView.as_view(), name="room-list"),
    # 특정 채팅방 상세 조회
    path("<int:room_id>/", RoomDetailView.as_view(), name="room-detail"),
]
