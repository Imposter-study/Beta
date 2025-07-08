# d:\poject_2506\Beta\accounts\migrations\0017_auto_20250708_1318.py

from django.db import migrations

# account_emailaddress 테이블의 user_id 컬럼 타입을 bigint에서 uuid로 변경하는 SQL
# User 모델의 PK가 uuid이므로, 이를 참조하는 ForeignKey도 uuid로 변경경
sql_statement = """
BEGIN;
-- 기존 Foreign Key 제약 조건 삭제
ALTER TABLE "account_emailaddress" DROP CONSTRAINT IF EXISTS "account_emailaddress_user_id_fkey";
ALTER TABLE "account_emailaddress" ALTER COLUMN "user_id" TYPE uuid USING "user_id"::text::uuid;

-- User 모델의 PK(uuid)를 참조하는 새로운 Foreign Key 제약 조건 추가
ALTER TABLE "account_emailaddress" ADD CONSTRAINT "account_emailaddress_user_id_fkey"
FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("uuid") ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
COMMIT;
"""

# 마이그레이션을 되돌릴 때 실행될 SQL (uuid -> bigint)
reverse_sql_statement = """
BEGIN;
ALTER TABLE "account_emailaddress" DROP CONSTRAINT IF EXISTS "account_emailaddress_user_id_fkey";
ALTER TABLE "account_emailaddress" ALTER COLUMN "user_id" TYPE bigint;
COMMIT;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0016_alter_user_nickname_alter_user_username"),
        ("account", "0002_email_max_length"),
    ]

    operations = [
        migrations.RunSQL(sql_statement, reverse_sql_statement),
    ]
