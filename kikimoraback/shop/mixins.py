from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


def is_staff_or_superuser(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class StaffCheckRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_staff_or_superuser(self.request.user)

    def handle_no_permission(self):
        return redirect("admin_login")
