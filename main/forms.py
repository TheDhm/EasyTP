from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import DefaultUser


class AddUsersCSV(forms.Form):
    csv_file = forms.FileField(label='csv file', max_length=200, allow_empty_file=False, required=True)
    role = forms.ChoiceField(label='choose role for users', choices=DefaultUser.ROLES, required=True)
    year = forms.ChoiceField(label='choose year for users', choices=DefaultUser.YEARS, required=True)


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(label='Role', choices=DefaultUser.ROLES, required=False)
    year = forms.ChoiceField(label='Year', choices=DefaultUser.YEARS, required=False)

    class Meta:
        model = DefaultUser
        fields = ("username", "email")

