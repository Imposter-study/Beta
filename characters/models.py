from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()

# TODO : 해시태그
class Character(models.Model):
    character = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="characters")

    # 필수
    title = models.CharField(max_length=20)
    name = models.CharField(max_length=10)

    # 임시 이미지 null=True, blank=True
    character_image = models.ImageField(
        upload_to="character/image/%Y/%m/%d/", null=True, blank=True
    )

    # 인트로 1500자 -> 리스트형식으로 
    # TODO : 베이스필드의 CharField의 max_length는 각각 하나의 리스트의 글자수를 제한하는것임
    # 총 글자를 1500자로 제한하려면 추가검증로직 필요
    intro = ArrayField(
    base_field=models.CharField(max_length=250),
    default=list,
    )   

    # 선택 필드

    # 캐릭터 설명 ( 캐릭터의 특징, 행동, 감정표현 등의 설명)
    character_info = models.TextField(null=True, blank=True)

    # 상세설명 ( 상황, 관계, 세계관 등의 설명)
    description = models.TextField(null=True, blank=True)

    # 상황예시 2000 -> 추가적인 인트로
    example_situation = ArrayField(
    base_field=models.CharField(max_length=250),
    default=list,
    blank=True,
    null=True,
    )

    # 소개글( 제목과 함께 보일 소개글 )
    presentation = models.TextField(max_length=40, null=True, blank=True)

    # 크리에이터 코멘트(유저에게 하고싶은 말)
    creator_comment = models.CharField(max_length=150, null=True, blank=True)

    # 시간 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 공개 여부
    is_character_public = models.BooleanField(default=True)
    is_description_public = models.BooleanField(default=True)
    is_example_public = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.name})"
