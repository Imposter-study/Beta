from django.urls import path
from . import views

urlpatterns = [
    path("", views.CharacterAPIView.as_view()),
    path("<int:pk>/", views.CharacterDetailAPIView.as_view()),
]
