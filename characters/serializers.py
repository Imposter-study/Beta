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

    # description과 example_public 공개여부에 따른 출력
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        is_owner = request and request.user == instance.user

        if not is_owner:
            # description은 TextField 로 None으로
            if not instance.is_description_public:
                representation["description"] = None
            # example_situation 필드는 ArrayField여서 빈 리스트로 반환
            if not instance.is_example_public:
                representation["example_situation"] = []

        return representation
