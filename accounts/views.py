from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny

# 소셜 로그인 관련
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.google import views as google_view

from accounts.docs.accounts_schemas import (
    signup_schema,
    user_profile_schema,
    my_profile_schema,
    update_profile_schema,
    deactivate_account_schema,
)

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)

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
    SocialSignupExtraSerializer,
)


# 회원가입, 회원조회, 회원수정, 회원탈퇴
class UserViewSet(GenericViewSet):
    queryset = User.objects.all()
    serializer_class = MyProfileSerializer
    lookup_field = "uuid"
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ["signup", "retrieve"]:
            permission_classes = [AllowAny]
        elif self.action in ["my_profile", "update_profile", "deactivate_account"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]

        permission_classes_list = []
        for permission in permission_classes:
            permission_classes_list.append(permission())
        return permission_classes_list

    # 회원가입
    @extend_schema(**signup_schema)
    @action(detail=False, methods=["post"], url_path="signup")
    def signup(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # 회원 조회 (기본 retrieve 오버라이드)
    @extend_schema(**user_profile_schema)
    def retrieve(self, _request, *_args, **_kwargs):
        instance = self.get_object()
        serializer = UserProfileSerializer(instance)
        return Response(serializer.data)

    # 내 프로필 조회 및 수정
    @extend_schema(methods=["GET"], **my_profile_schema)
    @extend_schema(methods=["PUT"], **update_profile_schema)
    @action(detail=False, methods=["get", "put"], url_path="my_profile")
    def my_profile(self, request):
        user = request.user
        if request.method == "GET":
            serializer = MyProfileSerializer(user)
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = MyProfileSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    # 회원 탈퇴
    @extend_schema(**deactivate_account_schema)
    @action(detail=False, methods=["post"], url_path="delete")
    def deactivate_account(self, request):
        user = request.user
        serializer = DeactivateAccountSerializer(
            user, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user.mark_as_deactivated()
        return Response(
            {"detail": "계정이 탈퇴 처리되었습니다. 90일 후 완전 삭제됩니다."},
            status=status.HTTP_200_OK,
        )


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
                    "uuid": str(user.uuid),
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
                    "uuid": user.uuid,
                    "access": access_token,
                    "refresh": refresh_token,
                },
                status=status.HTTP_200_OK,
            )

        # 기존 회원이면 토큰 포함 정상 로그인 응답
        response.data["is_signup"] = True
        response.data["uuid"] = user.uuid
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
                    "uuid": user.uuid,
                    "access": access_token,
                    "refresh": refresh_token,
                },
                status=status.HTTP_200_OK,
            )

        # 기존 회원이면 토큰 포함 정상 로그인 응답
        response.data["is_signup"] = True
        response.data["uuid"] = user.uuid
        response.data["access"] = access_token
        response.data["refresh"] = refresh_token
        return response


class SocialSignupAddInfoView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="소셜 회원가입 추가 정보 입력",
        description="소셜 로그인 후 추가 정보(성별, 생년월일 등)를 입력받아 회원 정보를 완성. 헤더에 JWT access 토큰 필요.",
        request=SocialSignupExtraSerializer,
        responses={
            200: OpenApiResponse(response=None, description="추가 정보 입력 완료"),
            400: OpenApiResponse(description="유효하지 않은 입력값"),
            401: OpenApiResponse(description="인증 실패(JWT 누락)"),
        },
        tags=["소셜 로그인"],
        examples=[
            OpenApiExample(
                name="요청 예시",
                value={"gender": "M", "birth_date": "1990-01-01"},
                request_only=True,
            ),
            OpenApiExample(
                name="응답 예시",
                value={"detail": "추가 정보 입력 완료"},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = SocialSignupExtraSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.gender = serializer.validated_data["gender"]
        user.birth_date = serializer.validated_data["birth_date"]
        user.save()
        return Response({"detail": "추가 정보 입력 완료"}, status=status.HTTP_200_OK)


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
        to_user_id = serializer.validated_data["uuid"]
        to_user = get_object_or_404(User, uuid=to_user_id)

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
    def put(self, request, chatprofile_uuid):
        profile = get_object_or_404(
            ChatProfile, uuid=chatprofile_uuid, user=request.user
        )
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
    def delete(self, request, chatprofile_uuid):
        profile = get_object_or_404(
            ChatProfile, uuid=chatprofile_uuid, user=request.user
        )
        profile.delete()
        return Response(status=204)
