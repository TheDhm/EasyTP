from django.contrib import admin
from .models import Containers, Instances, DefaultUser
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .forms import CustomUserCreationForm
from django.urls import path
from . import views


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

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('add_from_csv/', views.add_from_csv, name='add_from_csv')]
        return new_urls + urls


# admin.site.register(Containers)
# admin.site.register(Instances)
# Register your models here.
