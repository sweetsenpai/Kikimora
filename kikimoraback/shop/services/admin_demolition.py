class AdminDemotionService:
    def __init__(self, user):
        self.user = user

    def execute(self):
        """Снимает с пользователя права администратора, не удаляя его аккаунт."""
        if not self.user.is_staff and not self.user.is_superuser:
            raise ValueError("Пользователь уже не является администратором.")

        self.user.is_staff = False
        self.user.is_superuser = False
        self.user.save()
