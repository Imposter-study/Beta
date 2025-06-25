from django.urls import path
from .views import ChatRoomView, RoomListView, RoomDetailView

urlpatterns = [
    path("", ChatRoomView.as_view(), name="chat-room"),
    path("list/", RoomListView.as_view(), name="room-list"),
    path("<uuid:room_id>/", RoomDetailView.as_view(), name="room-detail"),
]
