from django.urls import path
from .views import RoomAPIView, ChatAPIView, ChatSuggestionAPIView, ChatRegenerateAPIView, RoomDetailAPIView

urlpatterns = [
    path("/", RoomAPIView.as_view()),
    path("messages/", ChatAPIView.as_view()),
    path("suggestions/", ChatSuggestionAPIView.as_view()),
    path("regenerate/", ChatRegenerateAPIView.as_view()),
    path("<uuid:room_id>/", RoomDetailAPIView.as_view()),
]
