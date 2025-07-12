from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers import MyProfileSerializer, UserProfileSerializer
from accounts.models import Follow


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
                "nickname": "testnickname1",
                "birth_date": "2000-01-01",
                "gender": "M",
                "introduce": "안녕하세요!!",
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
