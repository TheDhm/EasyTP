from django.contrib import admin, messages
from .models import AccessGroup


@admin.action(description='Change Access Group to 1CP')
def make_1cp(self, request, queryset):
    try:
        group = AccessGroup.objects.get(name=AccessGroup.CP1)
        queryset.update(group=group)
    except AccessGroup.DoesNotExist:
        messages.error(request, 'Group {} does not exist !'.format(AccessGroup.CP1))


@admin.action(description='Change Access Group to 2CP')
def make_2cp(self, request, queryset):
    try:
        group = AccessGroup.objects.get(name=AccessGroup.CP2)
        queryset.update(group=group)
    except AccessGroup.DoesNotExist:
        messages.error(request, 'Group {} does not exist !'.format(AccessGroup.CP2))


@admin.action(description='Change Access Group to 1CS')
def make_1cs(self, request, queryset):
    try:
        group = AccessGroup.objects.get(name=AccessGroup.CS1)
        queryset.update(group=group)
    except AccessGroup.DoesNotExist:
        messages.error(request, 'Group {} does not exist !'.format(AccessGroup.CS1))


@admin.action(description='Change Access Group to 2CS')
def make_2cs(self, request, queryset):
    try:
        group = AccessGroup.objects.get(name=AccessGroup.CS2)
        queryset.update(group=group)
    except AccessGroup.DoesNotExist:
        messages.error(request, 'Group {} does not exist !'.format(AccessGroup.CS2))
