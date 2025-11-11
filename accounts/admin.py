import jdatetime
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import UserCreationForm, UserChangeForm
from .models import MyUser, OtpCode


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ["full_name", "phone_number", "is_active", "is_admin"]
    list_filter = ["is_admin", "is_active", "is_staff"]

    fieldsets = [
        (None, {"fields": ["full_name", "phone_number", "password"]}),
        (_("Permissions"), {
            "fields": [
                "is_active", "is_admin", "is_staff", "is_superuser",
                "groups", "user_permissions"
            ]
        }),
        (_("Important dates"), {"fields": ["last_login"]}),
    ]

    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["full_name", "phone_number", "password1", "password2", "is_active", "is_admin"],
            },
        ),
    ]

    search_fields = ["full_name", "phone_number"]
    ordering = ["full_name"]
    filter_horizontal = ["groups", "user_permissions"]


admin.site.register(MyUser, UserAdmin)


@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ["phone_number", "code", "date_time_persian"]

    def date_time_persian(self, obj):
        return jdatetime.datetime.fromgregorian(datetime=obj.date_time_created).strftime("%Y/%m/%d %H:%M:%S")

    date_time_persian.short_description = _("Date/Time (Persian)")
    date_time_persian.admin_order_field = "date_time_created"
