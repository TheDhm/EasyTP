from django.contrib import admin
from .models import Containers, Instances, DefaultUser, AccessGroup, App
from django.contrib.auth.admin import UserAdmin, Group
from django.utils.translation import gettext_lazy as _
from .forms import CustomUserCreationForm, CustomAppForm
from django.urls import path
from . import views

admin.site.site_header = 'System Administration'


@admin.register(DefaultUser)
class CustomAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'is_staff', 'role', 'group', 'apps_available'
        )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('ROLE info'), {'fields': ('role', 'group')}),
        (_('Personal info'), {'fields': ('email', 'first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'group'),
        }),

    add_form = CustomUserCreationForm

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('add_from_csv/', views.add_from_csv, name='add_from_csv')]
        return new_urls + urls
    list_filter = ('is_staff', 'role', 'group')


class AccessGroupAdmin(admin.ModelAdmin):
    list_display = (
        'group',
        'has_access_to',
    )


class AppAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'groups',
    )
    form = CustomAppForm


# admin.site.register(Containers)
# admin.site.register(Instances)
admin.site.register(AccessGroup, AccessGroupAdmin)
admin.site.register(App, AppAdmin)
admin.site.unregister(Group)
# Register your models here.
