from django.contrib import admin
# Register your models here.
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission, User

from .models import Werktijd, Favoriet, UserSettings, ApiKey, OverurenAjust


class UserSettingsInline(admin.StackedInline):
    model = UserSettings
    can_delete = False


#@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserSettingsInline,)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()  # type: Set[str]

        readonly_fields = [
            'date_joined',
        ]

        if not is_superuser:
            disabled_fields |= {
                #'username',
                'is_superuser',
                'user_permissions',
                'is_staff',
            }

        # Prevent non-superusers from editing their own permissions
        if (
                not is_superuser
                and obj is not None
                and obj == request.user
        ):
            disabled_fields |= {
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


# Define a new User admin
# class UserAdmin(UserAdmin):
#     inlines = (UserSettingsInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Werktijd)
admin.site.register(Favoriet)
admin.site.register(Permission)
admin.site.register(ApiKey)
admin.site.register(OverurenAjust)
