from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers import MyProfileSerializer

# 회원 가입 테스트
class SignUpTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser1",
            password="1q2w3e4r!",
        )

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


#회원 조회(본인) 테스트
class UserProfileTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser1",
            password="1q2w3e4r!",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_user_profile(self):
        print("\n본인 조회 테스트")
        response = self.client.get(
            "/api/v1/accounts/my_profile/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        serializer = MyProfileSerializer(instance=self.user)
        print(serializer.data)
