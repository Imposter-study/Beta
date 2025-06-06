from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .models import User
from .serializers import SignUpSerializer, MyProfileSerializer, UserProfileSerializer


class UserCreateView(APIView):
    # 회원가입
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 내가 나의 프로필을 볼때, 타인의 프로필을 볼때
class UserProfileView(APIView):

    def get(self, request, nickname):
        user = get_object_or_404(User, nickname=nickname)

        if request.user.is_authenticated and request.user == user:
            serializer = MyProfileSerializer(user)
        else:
            serializer = UserProfileSerializer(user)

        return Response(serializer.data)


    def put(self, request, nickname):
        user = get_object_or_404(User, nickname=nickname)

        if request.user != user:
            raise PermissionDenied("수정 권한이 없습니다")
        serializer = MyProfileSerializer(user, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
