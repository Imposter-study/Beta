from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

# 소셜 로그인 관련
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.google import views as google_view

from .models import User, Follow, ChatProfile
from .serializers import (
    SignUpSerializer,
    MyProfileSerializer,
    UserProfileSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    DeactivateAccountSerializer,
    FollowSerializer,
    ChatProfileSerializer,
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
        summary="다른 유저 조회",
        description="본인 혹은 타인의 프로필을 조회합니다.",
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="로그인이 필요합니다."),
            404: OpenApiResponse(description="사용자를 찾을 수 없습니다."),
        },
    ),
)
# 내가 나의 프로필을 볼때, 타인의 프로필을 볼때
class UserProfileView(APIView):

    def get(self, request, nickname):
        user = get_object_or_404(User, nickname=nickname)

        serializer = UserProfileSerializer(user)

        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="사용자 프로필 조회",
        description="본인 프로필을 조회합니다.",
        responses={
            200: MyProfileSerializer,
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
class MyProfileView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        user = request.user
        serializer = MyProfileSerializer(user)

        return Response(serializer.data)

    def put(self, request):
        user = request.user

        serializer = MyProfileSerializer(user, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 로그인
class LoginView(APIView):
    @extend_schema(
        summary="로그인",
        description="아이디와 비밀번호를 입력해주세요(JWT 토큰, 닉네임 반환)",
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
                    "nickname": user.nickname,
                },
                status=status.HTTP_200_OK,
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
        description="비밀번호를 입력하여 계정을 탈퇴합니다",
        request=DeactivateAccountSerializer,
        responses={
            200: OpenApiResponse(description="탈퇴 완료."),
            400: OpenApiResponse(description="비밀번호가 일치하지 않습니다."),
        },
    )
    def post(self, request):
        serializer = DeactivateAccountSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            user.mark_as_deactivated()
            return Response(
                {"detail": "계정이 탈퇴 처리되었습니다. 90일 후 완전 삭제됩니다."},
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
        response = super().post(request, *args, **kwargs)

        user = request.user
        social_account = SocialAccount.objects.filter(
            user=user, provider="kakao"
        ).first()
        # JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # 프로필 정보가 아직 없는 경우
        if user.gender == "O" or not user.birth_date:
            return Response(
                {
                    "is_signup": False,
                    "kakao_id": social_account.uid,
                    "nickname": user.nickname,
                    "access": access_token,
                    "refresh": refresh_token,
                },
                status=status.HTTP_200_OK,
            )

        # 기존 회원이면 토큰 포함 정상 로그인 응답
        response.data["is_signup"] = True
        response.data["nickname"] = user.nickname
        response.data["access"] = access_token
        response.data["refresh"] = refresh_token
        return response


def kakao_redirect(request):
    code = request.GET.get("code")
    if code:
        return render(request, "accounts/redirect.html")
    return HttpResponse("로그인 실패. 코드가 없습니다.")


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
        response = super().post(request, *args, **kwargs)

        user = request.user
        social_account = SocialAccount.objects.filter(
            user=user, provider="google"
        ).first()

        # JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # 프로필 정보가 아직 없는 경우
        if user.gender == "O" or not user.birth_date:
            return Response(
                {
                    "is_signup": False,
                    "google_id": social_account.uid,
                    "nickname": user.nickname,
                    "access": access_token,
                    "refresh": refresh_token,
                },
                status=status.HTTP_200_OK,
            )

        # 기존 회원이면 토큰 포함 정상 로그인 응답
        response.data["is_signup"] = True
        response.data["nickname"] = user.nickname
        response.data["access"] = access_token
        response.data["refresh"] = refresh_token
        return response


# 팔로우/언팔로우 토글
class FollowToggleView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="팔로우/언팔로우 토글",
        description="한 번 누르면 팔로우, 또 누르면 언팔로우되는 토글 방식 API입니다.",
        request=FollowSerializer,
        responses={200: FollowSerializer},
    )
    def post(self, request):
        serializer = FollowSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from_user = request.user
        to_user_id = serializer.validated_data["user_id"]
        to_user = get_object_or_404(User, id=to_user_id)

        follow, created = Follow.objects.get_or_create(
            from_user=from_user, to_user=to_user
        )

        if created:
            response_serializer = FollowSerializer(follow)
            return Response(
                {"detail": "팔로우 성공", "data": response_serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            follow.delete()
            return Response({"detail": "언팔로우 성공"}, status=status.HTTP_200_OK)


# 대화프로필
@extend_schema(tags=["ChatProfile"])
class ChatProfileListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 대화 프로필 목록 조회",
        description="로그인한 사용자의 대화 프로필 목록을 반환합니다.",
        responses={200: ChatProfileSerializer(many=True)},
    )
    def get(self, request):
        profiles = ChatProfile.objects.filter(user=request.user)
        serializer = ChatProfileSerializer(profiles, many=True)
        return Response(serializer.data, status=200)

    @extend_schema(
        summary="대화 프로필 생성",
        description="새로운 대화 프로필을 생성합니다. 기본 프로필로 설정 시 기존 기본은 해제됩니다.",
        request=ChatProfileSerializer,
        responses={201: ChatProfileSerializer},
    )
    def post(self, request):
        serializer = ChatProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# 대화프로필 수정
@extend_schema(tags=["ChatProfile"])
class ChatProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="대화 프로필 수정",
        description="특정 대화 프로필을 수정합니다.",
        request=ChatProfileSerializer,
        responses={200: ChatProfileSerializer},
    )
    def put(self, request, chatprofile_id):
        profile = get_object_or_404(ChatProfile, id=chatprofile_id, user=request.user)
        serializer = ChatProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @extend_schema(
        summary="대화 프로필 삭제",
        description="특정 대화 프로필을 삭제합니다.",
        responses={204: None},
    )
    def delete(self, request, chatprofile_id):
        profile = get_object_or_404(ChatProfile, id=chatprofile_id, user=request.user)
        profile.delete()
        return Response(status=204)
