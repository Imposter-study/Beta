from drf_spectacular.utils import OpenApiResponse
from accounts.serializers import (
    UserProfileSerializer,
    MyProfileSerializer,
    DeactivateAccountSerializer,
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
