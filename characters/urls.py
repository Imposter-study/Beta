from django.urls import path
from . import views

urlpatterns = [
    path("", views.CharacterAPIView.as_view()),
    path("<int:pk>/", views.CharacterDetailAPIView.as_view()),
    path('search/', views.CharacterSearchAPIView.as_view()),
    path('scrap/<int:character_id>/', views.CharacterScrapAPIView.as_view()),
    path("myCharacters/", views.MyCharactersAPIView.as_view()),
]
