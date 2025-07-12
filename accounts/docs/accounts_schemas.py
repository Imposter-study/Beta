from drf_spectacular.utils import OpenApiResponse, OpenApiExample
from accounts.serializers import (
    UserProfileSerializer,
    MyProfileSerializer,
    DeactivateAccountSerializer,
    FollowSerializer,
    ChatProfileSerializer,
    SocialSignupExtraSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
)


signup_schema = dict(
    summary="회원가입",
    description=(
        "새로운 유저를 생성하는 API입니다.\n"
        "- multipart/form-data 형식으로 요청해야 하며,\n"
        "- 이미지 파일은 `profile_picture` 필드에 binary 형식으로 전달합니다."
    ),
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "사용자 ID"},
                "password": {"type": "string", "description": "비밀번호"},
                "password_confirm": {
                    "type": "string",
                    "description": "비밀번호 확인",
                },
                "nickname": {"type": "string", "description": "닉네임"},
                "birth_date": {
                    "type": "string",
                    "format": "date",
                    "description": "생년월일 YYYY-MM-DD",
                },
                "gender": {
                    "type": "string",
                    "enum": ["M", "F", "O"],
                    "description": "성별",
                },
                "introduce": {"type": "string", "description": "자기소개"},
                "profile_picture": {
                    "type": "string",
                    "format": "binary",
                    "description": "프로필 사진",
                },
            },
            "required": ["username", "password", "password_confirm"],
        }
    },
    responses={201: OpenApiResponse(description="회원가입 성공")},
)

user_profile_schema = dict(
    summary="회원 조회",
    description="특정 유저의 프로필을 조회하는 API입니다.",
    responses={
        200: UserProfileSerializer,
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(description="사용자를 찾을 수 없습니다."),
    },
)

my_profile_schema = dict(
    summary="내 프로필 조회",
    description="본인 프로필을 조회합니다.",
    responses={
        200: MyProfileSerializer,
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(description="사용자를 찾을 수 없습니다."),
    },
)

update_profile_schema = dict(
    summary="내 프로필 수정",
    description="본인 프로필을 수정하는 API입니다.",
    responses={
        200: MyProfileSerializer,
        400: OpenApiResponse(description="잘못된 요청입니다."),
        403: OpenApiResponse(description="수정 권한이 없습니다."),
        404: OpenApiResponse(description="사용자를 찾을 수 없습니다."),
    },
)

deactivate_account_schema = dict(
    summary="회원 탈퇴",
    description="회원탈퇴하는 API입니다. 비밀번호가 입력이 필요합니다.",
    request=DeactivateAccountSerializer,
    responses={
        200: OpenApiResponse(description="회원 탈퇴"),
        404: OpenApiResponse(description="사용자를 찾을 수 없습니다."),
    },
)


login_schema = dict(
    summary="로그인",
    description="아이디와 비밀번호를 입력해주세요(JWT 토큰,닉네임, UUID 반환)",
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(description="로그인 성공"),
        400: OpenApiResponse(description="올바른 아이디와, 비밀번호를 입력해주세요"),
    },
)

logout_schema = dict(
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
        200: OpenApiResponse(description="로그아웃 성공"),
        400: OpenApiResponse(description="유효하지 않은 토큰입니다."),
    },
)

password_change_schema = dict(
    summary="비밀번호 변경",
    description="이전비밀번호와 새로운 비밀번호 입력",
    request=PasswordChangeSerializer,
    responses={
        201: OpenApiResponse(description="비밀번호 변경 성공"),
        400: OpenApiResponse(description="올바른 이전 비밀번호를 입력해주세요"),
        405: OpenApiResponse(description="로그인해주세요(올바른 인증)"),
    },
)

social_signup_add_info_schema = dict(
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

follow_toggle_schema = dict(
    summary="팔로우/언팔로우 토글",
    description="한 번 누르면 팔로우, 또 누르면 언팔로우되는 토글 방식 API입니다.",
    request=FollowSerializer,
    responses={200: FollowSerializer},
)

chat_profile_list_create_schema = dict(
    summary="내 대화 프로필 목록 조회",
    description="로그인한 사용자의 대화 프로필 목록을 반환합니다.",
    responses={200: ChatProfileSerializer(many=True)},
)

chat_profile_create_schema = dict(
    summary="대화 프로필 생성",
    description="새로운 대화 프로필을 생성합니다. 기본 프로필로 설정 시 기존 기본은 해제됩니다.",
    request=ChatProfileSerializer,
    responses={201: ChatProfileSerializer},
)

chat_profile_detail_schema = dict(
    summary="대화 프로필 조회",
    description="특정 대화 프로필을 조회합니다.",
    responses={200: ChatProfileSerializer},
)

chat_profile_update_schema = dict(
    summary="대화 프로필 수정",
    description="특정 대화 프로필을 수정합니다.",
    request=ChatProfileSerializer,
    responses={200: ChatProfileSerializer},
)

chat_profile_delete_schema = dict(
    summary="대화 프로필 삭제",
    description="특정 대화 프로필을 삭제합니다.",
    responses={204: None},
)
