from rest_framework import serializers
from .models import Character, Hashtag


# 캐릭터 해시태그
class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ["tag_name"]


# 캐릭터 인트로
class CharacterIntroSerializer(serializers.Serializer):
    id = serializers.CharField()
    role = serializers.CharField()
    message = serializers.CharField()


# 캐릭터 상황예시
class CharacterExSituation(serializers.Serializer):
    id = serializers.CharField()
    role = serializers.CharField()
    message = serializers.CharField()


# 캐릭터 기본 정보
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
    hashtags = HashtagSerializer(many=True, read_only=True)

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
            "hashtags",
        ]
        read_only_fields = ["user"]


# 내가 캐릭터 생성자일때
class CharacterSerializer(CharacterBaseSerializer):
    is_character_public = serializers.BooleanField()
    is_description_public = serializers.BooleanField()
    is_example_public = serializers.BooleanField()
    hashtags = HashtagSerializer(many=True)
    
    class Meta(CharacterBaseSerializer.Meta):
        fields = CharacterBaseSerializer.Meta.fields + [
            "is_character_public",
            "is_description_public",
            "is_example_public",
            "hashtags",
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

    def create(self, validated_data):
        hashtag_data = validated_data.pop("hashtags", [])
        user = validated_data.pop("user", None)  # user가 있으면 제거
        if user is None:
            # context에서 user 가져오기 (백업)
            user = self.context["request"].user

        character = Character.objects.create(user=user, **validated_data)

        for tag_dict in hashtag_data:
            tag_name = tag_dict["tag_name"].lstrip("#")
            hashtag, created = Hashtag.objects.get_or_create(tag_name=tag_name)
            character.hashtags.add(hashtag)

        return character


# 다른사람이 캐릭터를 조회할때
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
