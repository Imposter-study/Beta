from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        provider = sociallogin.account.provider

        if provider == "kakao":
            kakao_uid = str(sociallogin.account.uid)
            kakao_nickname = data.get("properties", {}).get("nickname", "")

            user.username = kakao_uid
            user.nickname = kakao_nickname
            user.email = None
            user.set_unusable_password()
        return user
