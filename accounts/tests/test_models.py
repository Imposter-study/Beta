from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import User


class UserModelTest(TestCase):

    def test_generate_random_nickname(self):
        user = User.objects.create(username="testuser1")
        # 닉네임이 실제로 생성되었는지 검증
        self.assertIsNotNone(user.nickname)

    def test_mark_as_deactivated_sets_fields(self):
        user = User.objects.create(
            username="testuser2",
            email="test@example.com",
            gender="M",
            birth_date="2000-01-01",
            introduce="hello",
        )
        # mark_as_deactivated 메서드 호출, DB 리프레시
        user.mark_as_deactivated()
        user.refresh_from_db()

        # 정상적으로 변경되었는지 검증
        self.assertFalse(user.is_active)
        self.assertTrue(user.username.startswith("deleted_user_"))
        self.assertEqual(user.nickname, "탈퇴한 사용자")
        self.assertTrue(user.email.startswith("deleted_"))
        self.assertIsNone(user.introduce)
        self.assertIsNone(user.profile_picture)
        self.assertIsNone(user.birth_date)
        self.assertEqual(user.gender, "O")
        self.assertIsNotNone(user.deactivated_at)

    # is_ready_for_deletion 검증 로직
    # 1. deactivated_at가 90일 이상, 활성화 된 유저
    def test_is_ready_for_deletion_false_when_active(self):
        user = User.objects.create(username="activeuser")
        user.deactivated_at = timezone.now() - timedelta(days=100)
        user.save()
        self.assertFalse(user.is_ready_for_deletion())

    # 2. deactivated_at가 90일 미만, 비활성화 된 유저
    def test_is_ready_for_deletion_false_when_recently_deactivated(self):
        user = User.objects.create(username="recentinactive")
        user.is_active = False
        user.deactivated_at = timezone.now() - timedelta(days=10)
        user.save()
        self.assertFalse(user.is_ready_for_deletion())

    # 1. deactivated_at가 90일 이상, 비활성화 된 유저
    def test_is_ready_for_deletion_true_after_90_days(self):
        user = User.objects.create(username="longinactive")
        user.is_active = False
        user.deactivated_at = timezone.now() - timedelta(days=100)
        user.save()
        self.assertTrue(user.is_ready_for_deletion())
