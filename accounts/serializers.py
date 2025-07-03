from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from .models import ChatProfile, Follow



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


# 내가 나의 프로필 조회,수정
class MyProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(
        required=False
    )  # 명시적으로 선언해주면 Swagger가 더 잘 인식함

    class Meta:
        model = User
        fields = [
            "user_id",
            "username",
            "nickname",
            "introduce",
            "profile_picture",
        ]


# 타인의 프로필을 볼때
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "nickname",
            "profile_picture",
            "introduce",
        ]

# 탈퇴한 사용자 처리 포함 프로필 시리얼라이저
class UserPublicProfileSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "nickname",
            "profile_picture",
            "introduce",
        ]

    def get_nickname(self, obj):
        return obj.nickname if obj.is_active else "탈퇴한 사용자"

    def get_profile_picture(self, obj):
        return obj.profile_picture.url if obj.is_active and obj.profile_picture else None


# 대화프로필
class ChatProfileSerializer(serializers.ModelSerializer):
    chatprofile_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = ChatProfile
        fields = [
            "chatprofile_id",
            "user",
            "chat_nickname",
            "chat_description",
            "chat_profile_picture",
            "is_default",
        ]
        read_only_fields = ["chatprofile_id", "user"]


# 팔로우
class FollowSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Follow
        fields = ["user_id", "from_user", "to_user", "created_at"]
        read_only_fields = ["from_user", "created_at"]
