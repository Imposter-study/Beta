from rest_framework import serializers
from .models import Character


class CharacterIntroSerializer(serializers.Serializer):
    id = serializers.CharField()
    role = serializers.CharField()
    message = serializers.CharField()


class CharacterExSituation(serializers.Serializer):
    id = serializers.CharField()
    role = serializers.CharField()
    message = serializers.CharField()


class CharacterBaseSerializer(serializers.ModelSerializer):
    intro = serializers.ListField(
        child=CharacterIntroSerializer(),
        allow_empty=False,
    )
    example_situation = serializers.ListField(
        child=serializers.ListField(
            child=CharacterExSituation(),
            allow_empty=True,
        ),
        required=False,
        allow_empty=True,
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
        ]
        read_only_fields = ["user"]


class CharacterSerializer(CharacterBaseSerializer):
    is_character_public = serializers.BooleanField()
    is_description_public = serializers.BooleanField()
    is_example_public = serializers.BooleanField()

    class Meta(CharacterBaseSerializer.Meta):
        fields = CharacterBaseSerializer.Meta.fields + [
            "is_character_public",
            "is_description_public",
            "is_example_public",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")
        is_owner = request and request.user == instance.user

        if not is_owner:
            if not instance.is_description_public:
                representation["description"] = None
            if not instance.is_example_public:
                representation["example_situation"] = []

        return representation


class CharacterSearchSerializer(CharacterBaseSerializer):
    is_character_public = serializers.BooleanField()
    is_description_public = serializers.BooleanField()
    is_example_public = serializers.BooleanField()

    class Meta(CharacterBaseSerializer.Meta):
        fields = CharacterBaseSerializer.Meta.fields + [
            "is_character_public",
            "is_description_public",
            "is_example_public",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if not instance.is_description_public:
            representation["description"] = None
        if not instance.is_example_public:
            representation["example_situation"] = []

        return representation
