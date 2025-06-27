from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.http import Http404
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiParameter,
)
from .models import Character
from .serializers import (
    CharacterSerializer,
    CharacterSearchSerializer,
    CharacterBaseSerializer,
)


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
        description="캐릭터를 생성합니다.",
        request=CharacterSerializer,
        responses={
            201: CharacterSerializer,
            400: OpenApiResponse(description="잘못된 요청입니다."),
            401: OpenApiResponse(description="로그인이 필요합니다."),
        },
    ),
)
class CharacterAPIView(APIView):
    authentication_classes = [JWTAuthentication]

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

    def get_object(self, pk):
        character = get_object_or_404(Character, pk=pk)
        if character.user != self.request.user:
            raise PermissionDenied(
                "본인이 생성한 캐릭터만 조회, 수정, 삭제할 수 있습니다."
            )
        return character

    def get(self, request, pk):
        character = self.get_object(pk)
        serializer = CharacterSerializer(character, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk):
        character = self.get_object(pk)
        serializer = CharacterSerializer(
            character, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        character = self.get_object(pk)
        character.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# __icontains 특정 문자열이 포함 필터 (대소문자 구분x), __contains: 대소문자구별 문자포함
# distinct(): 중복검색 제거 ( 하나의 해시태그로 검색시 한캐릭이 여러번 검색될수있는 문제 )
class CharacterSearchAPIView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="name",
                type=str,
                location="query",
                description="검색할 캐릭터 이름 일부 문자열 (대소문자 구분 없이 포함 검색)",
                required=True,
            ),
        ],
        responses={
            200: CharacterSearchSerializer(many=True),
            404: OpenApiResponse(description="해당 이름의 캐릭터가 없습니다."),
        },
        description="이름 일부 문자열 포함하는 공개 캐릭터 목록 조회",
        tags=["Character"],
    )
    def get(self, request):
        query = request.query_params.get("name", "").strip()

        if not query:
            return Response(
                {"message": "한 글자 이상 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if query.startswith("#"):
            tag_name = query.lstrip("#")
            characters = Character.objects.filter(
                is_character_public=True,
                hashtags__tag_name__iexact=tag_name,
            ).distinct()
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
class MyCharactersAPIView(APIView):
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
