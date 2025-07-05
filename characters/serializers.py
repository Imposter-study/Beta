from rest_framework import serializers
from .models import Character, Hashtag
import json


# 캐릭터 해시태그
class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ["tag_name"]

        # 시리얼라이져의 중복검사 제외
        extra_kwargs = {
            "tag_name": {"validators": []},
        }


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
    creator_nickname = serializers.SerializerMethodField()

    class Meta:
        model = Character
        fields = [
            "character_id",
            "creator_nickname",
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

    def get_creator_nickname(self, obj):
        return obj.user.nickname


# 내가 캐릭터 생성자일때
class CharacterSerializer(CharacterBaseSerializer):
    is_character_public = serializers.BooleanField()
    is_description_public = serializers.BooleanField()
    is_example_public = serializers.BooleanField()
    hashtags = HashtagSerializer(many=True, required=False)
    room_number = serializers.SerializerMethodField()
    is_scrapped = serializers.SerializerMethodField()

    class Meta(CharacterBaseSerializer.Meta):
        fields = CharacterBaseSerializer.Meta.fields + [
            "is_character_public",
            "is_description_public",
            "is_example_public",
            "hashtags",
            "room_number",
            "is_scrapped",
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

    # 방번호 : 로그인시 캐릭터조회, 캐릭터와 대화했을경우 대화방번호 출력
    def get_room_number(self, obj):
        request = self.context.get("request")

        if request is None:
            return None
        if not request.user.is_authenticated:
            return None

        room = obj.rooms.filter(user=request.user).first()
        if room:
            return str(room.uuid)
        return None

    # 캐릭터 생성시 해시태그
    def create(self, validated_data):
        hashtag_data = validated_data.pop("hashtags", [])
        user = validated_data.pop("user", None)
        if user is None:
            user = self.context["request"].user

        character = Character.objects.create(user=user, **validated_data)

        for tag in hashtag_data:
            tag_name = tag["tag_name"].lstrip("#")
            hashtag, created = Hashtag.objects.get_or_create(tag_name=tag_name)
            character.hashtags.add(hashtag)

        return character

    # 캐릭터 수정시 해시태그
    def update(self, character, validated_data):
        hashtag_data = validated_data.pop("hashtags", None)

        character = super().update(character, validated_data)

        if hashtag_data is not None:
            character.hashtags.clear()
            for tag in hashtag_data:
                tag_name = tag["tag_name"].lstrip("#")
                hashtag, created = Hashtag.objects.get_or_create(tag_name=tag_name)
                character.hashtags.add(hashtag)

        return character

    def get_is_scrapped(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.scrapped_by.filter(id=request.user.id).exists()
        return False

    # multipart/form-data -> Json문자열 -> json.loads():딕서너리or리스트로 변환
    def to_internal_value(self, data):
        data = data.copy()
        for key in ["intro", "example_situation", "hashtags"]:
            value = data.get(key)
            if isinstance(value, str):
                try:
                    data[key] = json.loads(value)
                except json.JSONDecodeError:
                    raise serializers.ValidationError(
                        {key: f"{key}는 유효한 JSON 문자열이어야 합니다."}
                    )
        return super().to_internal_value(data)


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


# 유저 프로필 캐릭터 조회용
class UserProfileCharacterSerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Character
        fields = ["character_id", "title", "name", "character_image", "presentation", "hashtags"]
