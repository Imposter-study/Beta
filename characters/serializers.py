from rest_framework import serializers
from .models import Character


class CharacterSerializer(serializers.ModelSerializer):
    intro = serializers.ListField(
        child=serializers.CharField(max_length=250, allow_blank=True),
        allow_empty=False,
    )
    example_situation = serializers.ListField(
        child=serializers.CharField(max_length=250, allow_blank=True),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Character
        fields = [
            "name",
            "character_image",
            "title",
            "intro",
            "description",
            "character_info",
            "example_situation",
            "presentation",
            "creator_comment",
            "is_character_public",
            "is_description_public",
            "is_example_public",
        ]
        read_only_fields = ["user"]
