from django.test import TestCase
from django.contrib.auth import get_user_model


# 회원 가입 테스트
class SignUpTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser1",
            password="1q2w3e4r!",
        )

    # 회원가입 성공 테스트
    def test_signup_success(self):
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
        print("\n회원가입 성공")

    # 유저네임 중복 테스트
    def test_signup_username_duplicate(self):
        signup_data = {
            "username": "testuser1",
            "password": "1q2w3e4r!",
            "password_confirm": "1q2w3e4r!",
        }

        response = self.client.post(
            "/api/v1/accounts/signup/", signup_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400, "유저네임 중복")
        print("\n유저네임 중복")

    # 비밀번호 검증 테스트
    def test_signup_password_length(self):
        signup_data = {
            "username": "testuser2",
            "password": "1q2w4r!",
            "password_confirm": "1q2w4r!",
        }

        response = self.client.post(
            "/api/v1/accounts/signup/", signup_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        print("\n비밀번호 검증")

    # 비밀번호 일치 테스트
    def test_signup_password_mismatch(self):
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
        print("\n비밀번호 일치")
