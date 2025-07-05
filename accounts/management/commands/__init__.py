from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from accounts.models import User


class Command(BaseCommand):
    help = "90일 이상 비활성화된 유저를 완전히 삭제합니다."

    def handle(self, *args, **kwargs):
        threshold_date = timezone.now() - timedelta(days=90)
        users_to_delete = User.objects.filter(
            is_active=False, date_joined__lt=threshold_date
        )

        count = users_to_delete.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("삭제할 비활성 유저가 없습니다."))
        else:
            users_to_delete.delete()
            self.stdout.write(
                self.style.SUCCESS(f"{count}명의 유저를 완전히 삭제했습니다.")
            )


# 명령어 입력시 90일 지난 아이디를 삭제
# python manage.py delete_inactive_users
