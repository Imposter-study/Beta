from rest_framework import serializers
from .models import Character


class CharacterBaseSerializer(serializers.ModelSerializer):
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
        ]
        read_only_fields = ["user"]

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


class CharacterDetailSerializer(CharacterBaseSerializer):
    class Meta(CharacterBaseSerializer.Meta):
        fields = CharacterBaseSerializer.Meta.fields + [
            "is_character_public",
            "is_description_public",
            "is_example_public",
        ]

    # super(a, obj) 하면 a의 바로 위 클래스의 메서드를 호출 
    def to_representation(self, instance):
        return super(serializers.ModelSerializer, self).to_representation(instance)