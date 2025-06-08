from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from .serializers import SignUpSerializer, LoginSerializer, PasswordChangeSerializer, DeactivateAccountSerializer
from django.shortcuts import get_object_or_404
from django.utils import timezone


class UserCreateView(APIView):
    # 회원가입
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 로그인
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 로그아웃
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


# 비밀번호 수정
class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        user = request.user
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"detail": "Password changed successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# 회원 탈퇴
class DeactivateAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        serializer = DeactivateAccountSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.mark_as_deactivated()
            return Response({"detail": "Account deactivated. Will be permanently deleted after 90 days."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

