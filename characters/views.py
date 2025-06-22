from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)
from .models import Character
from .serializers import CharacterSerializer


@extend_schema_view(
    get=extend_schema(
        summary="캐릭터 조회",
        description="캐릭터를 조회합니다.",
        responses={
            200: CharacterSerializer,
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
# TODO : 모든캐릭터조회 > 요구사항정의서 추가
class CharacterAPIView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        characters = Character.objects.filter(is_character_public=True)
        serializer = CharacterSerializer(characters, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CharacterSerializer(data=request.data)
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
            raise PermissionDenied("본인이 생성한 캐릭터만 수정,삭제할 수 있습니다.")
        return character

    def get(self, request, pk):
        character = self.get_object(pk)
        serializer = CharacterSerializer(character)
        return Response(serializer.data)

    def put(self, request, pk):
        character = self.get_object(pk)
        serializer = CharacterSerializer(character, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        character = self.get_object(pk)
        character.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
