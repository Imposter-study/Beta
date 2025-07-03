from django.urls import path
from . import views

urlpatterns = [
    path("", views.CharacterAPIView.as_view()),
    path("<uuid:character_id>/", views.CharacterDetailAPIView.as_view()),
    path("search/", views.CharacterSearchAPIView.as_view()),
    path("scrap/<uuid:character_id>/", views.CharacterScrapAPIView.as_view()),
    path("my_scrap_characters/", views.MyScrapCharactersAPIView.as_view()),
    path("my_created_chracters/", views.MyCreateChracterAPIView.as_view()),
]
