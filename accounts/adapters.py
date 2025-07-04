from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        provider = sociallogin.account.provider

        if provider == "kakao":
            kakao_uid = str(sociallogin.account.uid)
            user.username = kakao_uid
            user.email = None
            user.set_unusable_password()

        elif provider == "google":
            google_uid = str(sociallogin.account.uid)
            user.username = google_uid
            user.set_unusable_password()
        return user
