from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient
from rest_framework.response import Response


from accounts.serializers import (
    MyProfileSerializer,
    UserProfileSerializer,
    ChatProfileSerializer,
)
from accounts.models import Follow, ChatProfile
from accounts.views import KakaoLogin

from allauth.socialaccount.models import SocialAccount
from unittest.mock import patch


# 테스트를 위한 기본 설정
class BaseTestCase(TestCase):
    def create_user(self, **kwargs):
        defaults = {
            "username": "testuser1",
            "password": "1q2w3e4r!",
        }
        defaults.update(kwargs)
        return get_user_model().objects.create_user(**defaults)

    def get_access_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)


# 회원 가입 테스트
class SignUpTest(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()

    # 회원가입 성공 테스트
    def test_signup_success(self):
        print("\n회원가입 테스트")
        # 회원가입 데이터 기입
        signup_data = {
            "username": "testuser2",
            "password": "1q2w3e4r!",
            "password_confirm": "1q2w3e4r!",
            # 선택 필드 예시 (필요시 추가)
            # "nickname": "테스트닉네임",
            # "birth_date": "2000-01-01",
            # "gender": "M",
            # "introduce": "안녕하세요"
        }
        response = self.client.post(
            "/api/v1/accounts/signup/", signup_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        User = get_user_model()
        self.assertTrue(User.objects.filter(username="testuser1").exists())

    # 유저네임 중복 테스트
    def test_signup_username_duplicate(self):
        print("\n유저네임 중복 테스트")
        signup_data = {
            "username": "testuser1",
            "password": "1q2w3e4r!",
            "password_confirm": "1q2w3e4r!",
        }
        response = self.client.post(
            "/api/v1/accounts/signup/", signup_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400, "유저네임 중복")

    # 비밀번호 검증 테스트
    def test_signup_password_length(self):
        print("\n비밀번호 검증 테스트")
        signup_data = {
            "username": "testuser2",
            "password": "1q2w4r!",
            "password_confirm": "1q2w4r!",
        }
        response = self.client.post(
            "/api/v1/accounts/signup/", signup_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    # 비밀번호 일치 테스트
    def test_signup_password_mismatch(self):
        print("\n비밀번호 일치 테스트")
        signup_data = {
            "username": "testuser2",
            "password": "1q2w3e4r!",
            # 다른 비밀번호
            "password_confirm": "2w3e4r",
        }
        response = self.client.post(
            "/api/v1/accounts/signup/", signup_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400, "비밀번호 일치")


# 본인 조회 테스트
class MyProfileTest(BaseTestCase):
    def setUp(self):
        self.user = self.create_user(
            nickname="테스트닉네임",
            birth_date="2000-01-01",
            gender="M",
            introduce="안녕하세요",
        )
        self.access_token = self.get_access_token(self.user)

    def test_user_profile(self):
        print("\n본인 조회 테스트")
        response = self.client.get(
            "/api/v1/accounts/my_profile/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        serializer = MyProfileSerializer(instance=self.user)
        print(serializer.data)

    def test_user_profile_fix(self):
        print("\n본인 프로필 수정 테스트")
        response = self.client.put(
            "/api/v1/accounts/my_profile/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={
                "nickname": "수정된 닉네임",
                "birth_date": "2000-01-01",
                "gender": "M",
                "introduce": "수정된 소개글",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        serializer = MyProfileSerializer(instance=self.user)
        print(serializer.data)


# 타인 조회 테스트
class UserProfileTest(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.access_token = self.get_access_token(self.user)

    def test_user_profile(self):
        print("\n타인 조회 테스트")
        other_user = self.create_user(username="other", password="1234test!")
        response = self.client.get(
            f"/api/v1/accounts/{other_user.uuid}/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        serializer = UserProfileSerializer(instance=other_user)
        print(serializer.data)


# 회원 탈퇴 테스트
class UserDeleteTest(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.access_token = self.get_access_token(self.user)

    def test_user_delete(self):
        print("\n회원 탈퇴 테스트")
        response = self.client.post(
            f"/api/v1/accounts/delete/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            data={"password": "1q2w3e4r!"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


# 로그인 테스트
class LoginTest(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.access_token = self.get_access_token(self.user)

    def test_login(self):
        print("\n로그인 테스트")
        response = self.client.post(
            f"/api/v1/accounts/signin/",
            data={"username": "testuser1", "password": "1q2w3e4r!"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_login_fail(self):
        print("\n로그인 실패 테스트")
        response = self.client.post(
            f"/api/v1/accounts/signin/",
            data={"username": "testuser1", "password": "틀린 비밀번호"},
        )
        self.assertEqual(response.status_code, 400)


# 로그아웃 테스트
class LogoutTest(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.access_token = self.get_access_token(self.user)
        self.refresh_token = RefreshToken.for_user(self.user)

    def test_logout(self):
        print("\n로그아웃 테스트")
        response = self.client.post(
            f"/api/v1/accounts/signout/",
            data={"refresh": str(self.refresh_token)},
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 205)

    def test_logout_fail(self):
        print("\n로그아웃 실패 테스트")
        response = self.client.post(
            f"/api/v1/accounts/signout/",
            data={"refresh": "invalid_refresh_token"},
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


# 비밀번호 수정 테스트
class PasswordChangeTest(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.access_token = self.get_access_token(self.user)

    def test_password_change(self):
        print("\n비밀번호 수정 테스트")
        response = self.client.put(
            f"/api/v1/accounts/password/",
            data={"old_password": "1q2w3e4r!", "new_password": "new_password"},
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new_password"))
        self.assertEqual(response.status_code, 200)


# 소셜 로그인 추가 정보 기입 테스트
class SocialSignupAddInfoTest(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.access_token = self.get_access_token(self.user)

    def test_social_signup_add_info(self):
        print("\n소셜 로그인 추가 정보 기입 테스트")
        response = self.client.post(
            f"/api/v1/accounts/social/signup/add_info/",
            data={"gender": "M", "birth_date": "2000-01-01"},
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)

    def test_social_signup_add_info_jwt_fail(self):
        print("\n소셜 로그인 추가 정보 기입 jwt 누락 테스트")
        response = self.client.post(
            f"/api/v1/accounts/social/signup/add_info/",
            data={"gender": "M", "birth_date": "2000-01-01"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_social_signup_add_info_invalid(self):
        print("\n소셜 로그인 추가 정보 기입 유효성 실패 테스트")
        response = self.client.post(
            f"/api/v1/accounts/social/signup/add_info/",
            data={"gender": "C", "birth_date": "2000-01-01"},
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


# 팔로우/언팔로우 토글 테스트
class FollowToggleTest(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.access_token = self.get_access_token(self.user)
        self.other_user = self.create_user(username="other", password="1234test!")

    def test_follow_toggle(self):
        print("\n팔로우/언팔로우 토글 테스트")
        response = self.client.post(
            f"/api/v1/accounts/follow/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={"uuid": self.other_user.uuid},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Follow.objects.count(), 1)
        # 언팔로우
        response = self.client.post(
            f"/api/v1/accounts/follow/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={"uuid": self.other_user.uuid},
        )
        # 언팔로우 시의 status_code는 구현에 따라 다를 수 있음(예: 204 No Content, 200 OK 등)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Follow.objects.count(), 0)


# 대화프로필 테스트
class ChatProfileTest(BaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.access_token = self.get_access_token(self.user)
        self.chat_profile = ChatProfile.objects.create(
            user=self.user, chat_nickname="미리 생성된 캐릭터"
        )

    def test_chat_profile_create(self):
        print("\n대화프로필 생성 테스트")
        response = self.client.post(
            f"/api/v1/accounts/chat_profiles/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={
                "chat_nickname": "캐릭터가 날 부르는 이름",
                "chat_description": "소개글",
                "is_default": False,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ChatProfile.objects.count(), 2)

    def test_chat_profile(self):
        print("\n대화프로필 조회 테스트")
        response = self.client.get(
            f"/api/v1/accounts/chat_profiles/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatProfile.objects.count(), 1)
        serializer = ChatProfileSerializer(instance=self.chat_profile)
        print(serializer.data)

    def test_chat_profile_update(self):
        print("\n대화프로필 수정 테스트")
        response = self.client.put(
            f"/api/v1/accounts/chat_profiles/{self.chat_profile.uuid}/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={
                "chat_nickname": "수정된 캐릭터가 날 부르는 이름",
                "chat_description": "수정된 소개글",
                "is_default": False,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatProfile.objects.count(), 1)
        self.chat_profile.refresh_from_db()
        serializer = ChatProfileSerializer(instance=self.chat_profile)
        print(serializer.data)

    def test_chat_profile_delete(self):
        print("\n대화프로필 삭제 테스트")
        response = self.client.delete(
            f"/api/v1/accounts/chat_profiles/{self.chat_profile.uuid}/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(ChatProfile.objects.count(), 0)


# 카카오 소셜 로그인 테스트
class KakaoLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.User = get_user_model()

    def test_kakao_login_complete_profile(self):
        """완성된 프로필을 가진 사용자의 카카오 로그인 테스트"""
        print("\n카카오 소셜 로그인 테스트(완성된 프로필)")

        # 완성된 프로필을 가진 사용자 생성
        test_user = self.User.objects.create_user(
            username="kakao_123456789",
            email="test@example.com",
            gender="M",  # 성별 설정됨
            birth_date="1990-01-01",  # 생년월일 설정됨
        )

        # SocialAccount 생성
        social_account = SocialAccount.objects.create(
            user=test_user, provider="kakao", uid="123456789"
        )

        # KakaoLogin view 직접 테스트
        factory = RequestFactory()
        request = factory.post(
            "/api/v1/accounts/kakao/login/", {"access_token": "fake_token"}
        )
        request.user = test_user

        # KakaoLogin view 인스턴스 생성
        view = KakaoLogin()
        view.request = request

        # 부모 클래스의 post 메서드를 mock하여 성공 응답 시뮬레이션
        with patch(
            "dj_rest_auth.registration.views.SocialLoginView.post"
        ) as mock_super:
            mock_super.return_value = Response(
                {"user": {"email": "test@example.com", "username": "kakao_123456789"}},
                status=200,
            )

            # 실제 KakaoLogin의 post 메서드 호출
            response = view.post(request)

        # 응답 검증
        print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("uuid", response.data)
        self.assertEqual(response.data["is_signup"], True)

        # SocialAccount 존재 검증
        self.assertTrue(
            SocialAccount.objects.filter(provider="kakao", uid="123456789").exists()
        )

    def test_kakao_login_incomplete_profile(self):
        """미완성 프로필을 가진 사용자의 카카오 로그인 테스트"""
        print("\n카카오 소셜 로그인 테스트(미완성 프로필)")

        # 미완성 프로필을 가진 사용자 생성
        test_user = self.User.objects.create_user(
            username="kakao_987654321",
            email="incomplete@example.com",
            gender="O",  # 미설정 상태
            birth_date=None,  # 미설정 상태
        )

        # SocialAccount 생성
        social_account = SocialAccount.objects.create(
            user=test_user, provider="kakao", uid="987654321"
        )

        factory = RequestFactory()
        request = factory.post(
            "/api/v1/accounts/kakao/login/", {"access_token": "fake_token"}
        )
        request.user = test_user

        # KakaoLogin view 인스턴스 생성
        view = KakaoLogin()
        view.request = request

        # 부모 클래스의 post 메서드를 mock하여 성공 응답 시뮬레이션
        with patch(
            "dj_rest_auth.registration.views.SocialLoginView.post"
        ) as mock_super:
            mock_super.return_value = Response(
                {
                    "user": {
                        "email": "incomplete@example.com",
                        "username": "kakao_987654321",
                    }
                },
                status=200,
            )

            # 실제 KakaoLogin의 post 메서드 호출
            response = view.post(request)

        # 응답 검증 - 미완성 프로필은 is_signup: False
        print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("kakao_id", response.data)
        self.assertEqual(response.data["is_signup"], False)
        self.assertEqual(response.data["kakao_id"], "987654321")

        # SocialAccount 존재 검증
        self.assertTrue(
            SocialAccount.objects.filter(provider="kakao", uid="987654321").exists()
        )
