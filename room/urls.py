from django.urls import path
from .views import ChatAPIView, RoomAPIView, RoomDetailAPIView

urlpatterns = [
    path("", ChatAPIView.as_view()),
    path("list/", RoomAPIView.as_view()),
    path("<uuid:room_id>/", RoomDetailAPIView.as_view()),
]
