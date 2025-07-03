from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import requests
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.models import SocialAccount
from django.http import JsonResponse
from allauth.socialaccount.providers.google import views as google_view
from uuid import UUID

from .models import User, ChatProfile, Follow
from .serializers import (
    SignUpSerializer,
    MyProfileSerializer,
    UserProfileSerializer,
    UserPublicProfileSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    DeactivateAccountSerializer,
    ChatProfileSerializer,
    FollowSerializer,
)
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
        responses={201: OpenApiResponse(description="회원가입 성공")},
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
            401: OpenApiResponse(description="로그인이 필요합니다."),
            404: OpenApiResponse(description="사용자를 찾을 수 없습니다."),
        },
    ),
    put=extend_schema(
        summary="사용자 프로필 수정",
        description="본인 프로필을 수정합니다. 타인은 수정 불가.",
        request=MyProfileSerializer,
        responses={
            200: MyProfileSerializer,
            400: OpenApiResponse(description="잘못된 요청입니다."),
            403: OpenApiResponse(description="수정 권한이 없습니다."),
            404: OpenApiResponse(description="사용자를 찾을 수 없습니다."),
        },
    ),
)


# 본인 프로필 조회 및 수정
class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        serializer = MyProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = MyProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 타인 프로필 조회
class PublicProfileView(APIView):
    def get(self, request, user_id):
        user = get_object_or_404(User, user_id=user_id)
        serializer = UserPublicProfileSerializer(user)
        return Response(serializer.data)


# 로그인
class LoginView(APIView):
    @extend_schema(
        summary="로그인",
        description="아이디와 비밀번호를 입력해주세요(JWT 토큰 반환)",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="로그인 성공"),
            400: OpenApiResponse(
                description="올바른 아이디와, 비밀번호를 입력해주세요"
            ),
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
                    "refresh": {"type": "string", "example": "qweasdzxc..."},
                },
                "required": ["refresh"],
            }
        },
        responses={
            200: OpenApiResponse(description="로그아웃 성공!"),
            400: OpenApiResponse(description="유효하지 않은 토큰입니다!!"),
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
            201: OpenApiResponse(description="비밀번호 변경 성공"),
            400: OpenApiResponse(description="올바른 이전 비밀번호를 입력해주세요"),
            405: OpenApiResponse(description="로그인해주세요(올바른 인증)"),
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
            200: OpenApiResponse(description="Account deactivated."),
            400: OpenApiResponse(description="비밀번호가 일치하지 않습니다."),
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


# 카카오 소셜 로그인
class KakaoLogin(SocialLoginView):
    adapter_class = kakao_view.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.SOCIALACCOUNT_PROVIDERS["kakao"]["APP"]["redirect_uri"]

    @extend_schema(
        summary="카카오 소셜 로그인",
        description="카카오 OAuth2 인증을 통해 소셜 로그인을 수행합니다.",
        responses={
            200: OpenApiResponse(
                description="로그인 성공. JWT 토큰 등 인증 정보 반환."
            ),
            400: OpenApiResponse(
                description="인증 실패. 잘못된 토큰 또는 유효하지 않은 요청."
            ),
        },
        tags=["소셜 로그인"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# 구글 소셜 로그인
class GoogleLogin(SocialLoginView):
    adapter_class = google_view.GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["redirect_uri"]

    @extend_schema(
        summary="구글 소셜 로그인",
        description="구글 OAuth2 인증을 통해 소셜 로그인을 수행합니다.",
        responses={
            200: OpenApiResponse(
                description="로그인 성공. JWT 토큰 등 인증 정보 반환."
            ),
            400: OpenApiResponse(
                description="인증 실패. 잘못된 토큰 또는 유효하지 않은 요청."
            ),
        },
        tags=["소셜 로그인"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# 대화프로필
@extend_schema(tags=["ChatProfile"])
class ChatProfileView(APIView):
    permission_classes = [IsAuthenticated]
    # parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="내 대화 프로필 목록 조회",
        description="로그인한 사용자의 대화 프로필 목록을 반환합니다.",
        responses={200: ChatProfileSerializer(many=True)},
    )
    def get(self, request):
        profiles = ChatProfile.objects.filter(user=request.user)
        serializer = ChatProfileSerializer(profiles, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="새 대화 프로필 생성",
        description="새로운 대화 프로필을 생성합니다.",
        request=ChatProfileSerializer,
        responses={201: ChatProfileSerializer},
    )
    def post(self, request):
        serializer = ChatProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# 기본대화프로필
@extend_schema(tags=["ChatProfile"])
class ChatProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]
    # parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="대화 프로필 수정",
        description="특정 대화 프로필을 수정합니다.",
        request=ChatProfileSerializer,
        responses={200: ChatProfileSerializer},
    )
    def put(self, request, chatprofile_uuid):
        profile = get_object_or_404(
            ChatProfile, uuid=chatprofile_uuid, user=request.user
        )
        serializer = ChatProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @extend_schema(
        summary="대화 프로필 삭제",
        description="특정 대화 프로필을 삭제합니다.",
        responses={204: None},
    )
    def delete(self, request, chatprofile_id):
        profile = get_object_or_404(
            ChatProfile, chatprofile_id=chatprofile_id, user=request.user
        )
        profile.delete()
        return Response(status=204)


# 팔로우
@extend_schema(
    summary="팔로우 생성",
    description="현재 로그인한 사용자가 다른 사용자를 팔로우합니다.",
    request=FollowSerializer,
    responses={201: FollowSerializer},
)
class FollowCreateView(generics.CreateAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)


# 언팔로우
@extend_schema(
    summary="언팔로우",
    description="현재 로그인한 사용자가 특정 유저를 언팔로우합니다. `to_user_id`는 언팔로우할 유저의 ID입니다.",
    responses={
        204: None,
        404: {"detail": "팔로우 관계가 없습니다."},
    },
)
class UnfollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, to_user_id):
        try:
            follow = Follow.objects.get(from_user=request.user, to_user_id=to_user_id)
            follow.delete()
            return Response(
                {"detail": "언팔로우 성공"}, status=status.HTTP_204_NO_CONTENT
            )
        except Follow.DoesNotExist:
            return Response(
                {"detail": "팔로우 관계가 없습니다."}, status=status.HTTP_404_NOT_FOUND
            )


# 팔로우/팔로워 수 조회
@extend_schema(
    summary="팔로우 수 조회",
    description="해당 유저의 팔로잉 수와 팔로워 수를 조회합니다. `user_id`는 대상 유저의 ID입니다.",
    responses={
        200: {
            "type": "object",
            "properties": {
                "user": {"type": "string", "description": "닉네임"},
                "팔로잉": {"type": "integer"},
                "팔로워": {"type": "integer"},
            },
        },
        404: {"detail": "해당 유저가 존재하지 않습니다."},
    },
)
class FollowCountView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)
            following_count = user.following.count()
            followers_count = user.followers.count()
            return Response(
                {
                    "user": user.nickname if user.is_active else "탈퇴한 사용자",
                    "팔로잉": following_count,
                    "팔로워": followers_count,
                }
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "해당 유저가 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
