from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .custom_validators import validate_year
from .models import DefaultUser

all_Years = [('', None)] + DefaultUser.YEARS


class AddUsersCSV(forms.Form):
    csv_file = forms.FileField(label='csv file', max_length=200, allow_empty_file=False, required=True)
    role = forms.ChoiceField(label='choose role for users', choices=DefaultUser.ROLES, required=True)
    year = forms.ChoiceField(label='choose year for users', choices=all_Years, required=False)

    def clean_year(self):
        role = self.cleaned_data.get('role')
        year = self.cleaned_data.get('year')
        validate_year(role, year)


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(label='Role', choices=DefaultUser.ROLES, required=False)
    year = forms.ChoiceField(label='Year', choices=all_Years, required=False)

    class Meta:
        model = DefaultUser
        fields = ("username", "email")

    def clean_year(self):
        role = self.cleaned_data.get('role')
        year = self.cleaned_data.get('year')
        validate_year(role, year)

