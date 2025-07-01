from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from characters.serializers import UserProfileCharacterSerializer

User = get_user_model()


# 회원가입
class SignUpSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)
    nickname = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "password_confirm",
            "nickname",
            "birth_date",
            "gender",
            "introduce",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = self.Meta.model(**validated_data)

        user.set_password(password)
        user.is_active = True
        user.save()
        return user

    # 유저네임 검증
    def validate_username(self, value):
        if not value:
            raise serializers.ValidationError("아이디를 입력해주세요.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 존재하는 아이디입니다.")
        return value

    # 비밀번호 검증
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("비밀번호는 최소 8자 이상이어야 합니다.")
        return value

    # 비밀번호 확인 및 일치 여부 검증
    def validate(self, data):
        password = data.get("password")
        password_confirm = data.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "비밀번호가 일치하지 않습니다."}
            )

        return data


# 로그인
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")


# 비밀번호 변경
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


# 회원 탈퇴
class DeactivateAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return value


# 타인 프로필 조회
class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False)
    characters = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "nickname",
            "introduce",
            "profile_picture",
            "characters",
        ]

    def get_characters(self, obj):
        queryset = obj.characters.filter(is_character_public=True)
        return UserProfileCharacterSerializer(queryset, many=True).data


# 내 프로필 조회
class MyProfileSerializer(UserProfileSerializer):
    class Meta(UserProfileSerializer.Meta):
        fields = UserProfileSerializer.Meta.fields + [
            "birth_date",
            "gender",
        ]

    def get_characters(self, obj):
        queryset = obj.characters.all()
        return UserProfileCharacterSerializer(queryset, many=True).data
