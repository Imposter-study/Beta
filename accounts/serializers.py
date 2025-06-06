from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "password_confirm",
            "nickname",
            "age",
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
        user.is_active = False
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


# 내가 나의 프로필 조회,수정
class MyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "nickname",
            "age",
            "gender",
            "introduce",
        ]


# 타인의 프로필을 볼때
# TODO: 타인의 프로필을 볼때 만든 캐릭터 필드 추가
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "nickname",
        ]
