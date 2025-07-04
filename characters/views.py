from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.http import Http404
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample
)
from .models import Character
from .serializers import (
    CharacterSerializer,
    CharacterSearchSerializer,
    CharacterBaseSerializer,
)
import re
from django.db.models import Q


@extend_schema_view(
    get=extend_schema(
        summary="캐릭터 조회",
        description="캐릭터를 조회합니다.",
        responses={
            200: CharacterBaseSerializer,
        },
    ),
    post=extend_schema(
        summary="캐릭터 생성",
        description=(
            "multipart/form-data 형식으로 캐릭터를 생성합니다.\n"
            "- 이미지 파일은 `character_image` 필드에 업로드합니다.\n"
            "- `intro`, `example_situation`, `hashtags` 필드는 JSON 문자열로 전달해야 합니다.\n"
            "- `hashtags`는 `[{\"tag_name\":\"#예시\"}, ...]` 형태입니다."
        ),
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string', 'maxLength': 20, 'description': '캐릭터 제목'},
                    'name': {'type': 'string', 'maxLength': 10, 'description': '캐릭터 이름'},
                    'character_image': {'type': 'string', 'format': 'binary', 'description': '캐릭터 이미지 파일'},
                    'intro': {'type': 'string', 'description': '인트로 JSON 문자열'},
                    'example_situation': {'type': 'string', 'description': '상황예시 JSON 문자열'},
                    'character_info': {'type': 'string', 'description': '캐릭터 정보'},
                    'description': {'type': 'string', 'description': '상세 설명'},
                    'presentation': {'type': 'string', 'maxLength': 40, 'description': '소개글'},
                    'creator_comment': {'type': 'string', 'maxLength': 150, 'description': '크리에이터 코멘트'},
                    'is_character_public': {'type': 'boolean', 'description': '캐릭터 공개 여부'},
                    'is_description_public': {'type': 'boolean', 'description': '상세설명 공개 여부'},
                    'is_example_public': {'type': 'boolean', 'description': '상황예시 공개 여부'},
                    'hashtags': {'type': 'string', 'description': '해시태그 JSON 문자열'},
                },
                'required': ['title', 'name', 'intro'],
            }
        },
        responses={
            201: OpenApiResponse(response=CharacterSerializer, description="캐릭터 생성 성공"),
            400: OpenApiResponse(description="잘못된 요청입니다."),
            401: OpenApiResponse(description="로그인이 필요합니다."),
        },
        examples=[
            OpenApiExample(
                '캐릭터 생성 예시',
                value={
                    'title': '마법사',
                    'name': '헤르미온느',
                    'intro': '[{"id":"1","role":"system","message":"안녕하세요"}]',
                    'example_situation': '[ [{"id":"1","role":"user","message":"예시 상황입니다."}] ]',
                    'character_info': '마법에 능한 소녀',
                    'description': '마법 세계에서 모험하는 캐릭터',
                    'presentation': '친절한 마법사',
                    'creator_comment': '즐겁게 사용해주세요',
                    'is_character_public': True,
                    'is_description_public': True,
                    'is_example_public': True,
                    'hashtags': '[{"tag_name":"#마법사"}, {"tag_name":"#모험"}]',
                },
                media_type='application/json',
            )
        ],
    ),
)
class CharacterAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        characters = Character.objects.filter(is_character_public=True)
        serializer = CharacterBaseSerializer(
            characters, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = CharacterSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        summary="특정 캐릭터 조회",
        description="PK 값으로 특정 캐릭터를 조회합니다",
        responses={
            200: CharacterSerializer,
            401: OpenApiResponse(description="로그인이 필요합니다."),
            403: OpenApiResponse(description="접근 권한이 없습니다."),
            404: OpenApiResponse(description="캐릭터를 찾을 수 없습니다."),
        },
    ),
    put=extend_schema(
        summary="캐릭터 수정",
        description="PK 값으로 특정 캐릭터를 수정합니다",
        request=CharacterSerializer,
        responses={
            200: CharacterSerializer,
            400: OpenApiResponse(description="잘못된 요청입니다."),
            401: OpenApiResponse(description="로그인이 필요합니다."),
            403: OpenApiResponse(description="접근 권한이 없습니다."),
            404: OpenApiResponse(description="캐릭터를 찾을 수 없습니다."),
        },
    ),
    delete=extend_schema(
        summary="캐릭터 삭제",
        description="PK 값으로 특정 캐릭터를 삭제합니다",
        responses={
            204: OpenApiResponse(description="삭제 완료"),
            401: OpenApiResponse(description="로그인이 필요합니다."),
            403: OpenApiResponse(description="접근 권한이 없습니다."),
            404: OpenApiResponse(description="캐릭터를 찾을 수 없습니다."),
        },
    ),
)
class CharacterDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, character_id):
        character = get_object_or_404(Character, pk=character_id)
        if character.user != self.request.user:
            raise PermissionDenied("본인이 생성한 캐릭터만 조회, 수정, 삭제할 수 있습니다.")
        return character

    def get(self, request, character_id):
        character = self.get_object(character_id)
        serializer = CharacterSerializer(character, context={"request": request})
        return Response(serializer.data)

    def put(self, request, character_id):
        character = self.get_object(character_id)
        serializer = CharacterSerializer(
            character, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, character_id):
        character = self.get_object(character_id)
        character.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# __icontains 특정 문자열이 포함 필터 (대소문자 구분x), __contains: 대소문자구별 문자포함
# distinct(): 중복검색 제거 ( 하나의 해시태그로 검색시 한캐릭이 여러번 검색될수있는 문제 )
# 현재 해시태그 #안에는 띄어쓰기가 없어야함
class CharacterSearchAPIView(APIView):
    @extend_schema(
        summary="이름,해시태그로 캐릭터 검색",
        parameters=[
            OpenApiParameter(
                name="name",
                type=str,
                location="query",
                description="캐릭터 이름 또는 해시태그로 캐릭터검색",
                required=True,
            ),
        ],
        responses={
            200: CharacterSearchSerializer(many=True),
            404: OpenApiResponse(description="해당 이름의 캐릭터가 없습니다."),
        },
        description="이름 일부, 해시태그 포함하는 공개 캐릭터 목록 조회",
    )
    def get(self, request):
        query = request.query_params.get("name", "").strip()

        if not query:
            return Response(
                {"message": "한 글자 이상 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 해시태그 검색 ( 정규식으로 # 붙은 이름 추출 )
        if query.startswith("#"):
            tag_names = re.findall(r"#(\S+)", query)

            if not tag_names:
                return Response(
                    {"message": "유효한 해시태그를 입력해주세요."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            q = Q()
            for tag in tag_names:
                q |= Q(hashtags__tag_name__iexact=tag)

            characters = (
                Character.objects.filter(is_character_public=True).filter(q).distinct()
            )

        # 이름 검색
        else:
            characters = Character.objects.filter(
                is_character_public=True, name__icontains=query
            )

        if not characters.exists():
            raise Http404("해당 조건의 캐릭터가 없습니다.")

        serializer = CharacterSearchSerializer(
            characters, many=True, context={"request": request}
        )
        return Response(serializer.data)


@extend_schema_view(
    post=extend_schema(
        summary="캐릭터 스크랩(팔로우)",
        description="로그인한 사용자가 특정 캐릭터 스크랩(팔로우, 언팔) 토글",
        responses={
            200: OpenApiResponse(description="스크랩 완료 또는 취소"),
            401: OpenApiResponse(description="인증이 필요합니다."),
            404: OpenApiResponse(description="해당 캐릭터를 찾을 수 없습니다."),
        },
    ),
)
# 캐릭터 스크랩(팔로우)
class CharacterScrapAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, character_id):
        character = get_object_or_404(Character, pk=character_id)
        user = request.user

        if user in character.scrapped_by.all():
            character.scrapped_by.remove(user)
            return Response({"detail": "스크랩 취소!"}, status=status.HTTP_200_OK)
        else:
            character.scrapped_by.add(user)
            return Response({"detail": "스크랩 완료!"}, status=status.HTTP_200_OK)


@extend_schema(
    summary="내가 스크랩한 캐릭터 목록 조회",
    description="로그인 사용자가 스크랩한 캐릭터들 중 공개된 캐릭터 조회.",
    responses={
        200: CharacterBaseSerializer(many=True),
        401: OpenApiResponse(description="로그인이 필요합니다."),
    },
)
# 내가 스크랩(팔로우한 캐릭터 조회)
class MyScrapCharactersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        characters = user.scrapped_characters.filter(is_character_public=True).order_by(
            "-created_at"
        )
        serializer = CharacterBaseSerializer(
            characters, many=True, context={"request": request}
        )
        return Response(serializer.data)


@extend_schema(
    summary="내가 생성한 모든 캐릭터 조회",
    description="내가 만든 모든 캐릭터 조회",
    responses={
        200: CharacterBaseSerializer(many=True),
        401: OpenApiResponse(description="로그인이 필요합니다."),
    },
)
# 내가 생성한 캐릭터들 조회
class MyCreateChracterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        characters = user.characters.all().order_by("-created_at")
        serializer = CharacterSerializer(
            characters, many=True, context={"request": request}
        )
        return Response(serializer.data)
