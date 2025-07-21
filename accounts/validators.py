# accounts/validators.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


def validate_username(value):
    if not value:
        raise serializers.ValidationError("아이디를 입력해주세요.")
    if User.objects.filter(username=value).exists():
        raise serializers.ValidationError("이미 존재하는 아이디입니다.")
    return value


def validate_password(value):
    if len(value) < 8:
        raise serializers.ValidationError("비밀번호는 최소 8자 이상이어야 합니다.")
    return value


def validate_passwords_confirm(data):
    password = data.get("password")
    password_confirm = data.get("password_confirm")
    if password != password_confirm:
        raise serializers.ValidationError(
            {"password_confirm": "비밀번호가 일치하지 않습니다."}
        )
    return data
