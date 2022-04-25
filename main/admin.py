from django.contrib import admin
from .models import Containers, Instances, DefaultUser
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .forms import CustomUserCreationForm


@admin.register(DefaultUser)
class CustomAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'is_staff', 'role', 'year'
        )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('ROLE info'), {'fields': ('role', 'year')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'role', 'year'),
        }),

    add_form = CustomUserCreationForm


# admin.site.register(Containers)
# admin.site.register(Instances)
# Register your models here.
