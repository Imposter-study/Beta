from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .models import User
from .serializers import SignUpSerializer, MyProfileSerializer, UserProfileSerializer
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from .serializers import (
    SignUpSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    DeactivateAccountSerializer,
)
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)


class UserCreateView(APIView):
    @extend_schema(
        summary="회원가입",
        description="새로운 ExampleModel을 생성하는 API입니다.",
        request=SignUpSerializer,
        responses={201: SignUpSerializer},
    )
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary="사용자 프로필 조회",
        description="본인 혹은 타인의 프로필을 조회합니다.",
        responses={
            200: UserProfileSerializer,
            401: {"message": "로그인이 필요합니다."},
            404: {"message": "사용자를 찾을 수 없습니다."},
        },
    ),
    put=extend_schema(
        summary="사용자 프로필 수정",
        description="본인 프로필을 수정합니다. 타인은 수정 불가.",
        request=MyProfileSerializer,
        responses={
            200: MyProfileSerializer,
            400: {"message": "잘못된 요청입니다."},
            403: {"message": "수정 권한이 없습니다."},
            404: {"message": "사용자를 찾을 수 없습니다."},
        },
    ),
)
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


# 로그인
class LoginView(APIView):
    @extend_schema(
        summary="로그인",
        description="아이디와 비밀번호를 입력해주세요(JWT 토큰 반환)",
        request=LoginSerializer,
        responses={
            200: LoginSerializer,
            400: {"message": "올바른 아이디와, 비밀번호를 입력해주세요"},
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 로그아웃
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="로그아웃",
        description="리프레시 토큰을 받아 블랙리스트 등록",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "refresh": {"type": "string", "example": "qweasdzxc..."}
                },
                "required": ["refresh"],
            }
        },
        responses={
            200: {"detail": "로그아웃 성공!"},
            400: {"detail": "유효하지 않은 토큰입니다!!"},
        },
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception as e:
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )


# 비밀번호 수정
class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="비밀번호 변경",
        description="이전비밀번호와 새로운 비밀번호 입력",
        request=PasswordChangeSerializer,
        responses={
            201: PasswordChangeSerializer,
            400: {"message": "올바른 이전 비밀번호를 입력해주세요"},
            405: {"message": "로그인해주세요(올바른 인증)"},
        },
    )
    def put(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        user = request.user
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data["old_password"]):
                return Response(
                    {"detail": "Old password is incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response({"detail": "Password changed successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 회원 탈퇴
class DeactivateAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="회원탈퇴!!!",
        description="비밀번호 입력해주세요",
        request=DeactivateAccountSerializer,
        responses={
            200: {"detail": "Account deactivated."},
            400: {"message": "비밀번호가 일치하지 않습니다."},
        },
    )
    def delete(self, request):
        serializer = DeactivateAccountSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            user.mark_as_deactivated()
            return Response(
                {
                    "detail": "Account deactivated. Will be permanently deleted after 90 days."
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
