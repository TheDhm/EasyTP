from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import DefaultUser, AccessGroup, App, UsersFromCSV
from django.core.validators import FileExtensionValidator


class UsersFromCSVForm(forms.ModelForm):
    class Meta:
        model = UsersFromCSV
        fields = "__all__"
        help_texts = {
            'file': 'Upload a file .csv or .xls, containing a list of new users',
            'role': 'Specify the role of new users',
            'group': 'Specify the access group of new users'
        }


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(label='Role', choices=DefaultUser.ROLES, required=True)
    group = forms.ModelChoiceField(AccessGroup.objects.all(), label='group', required=True)

    class Meta:
        model = DefaultUser
        fields = ("username", "email")


class CustomAppForm(forms.ModelForm):
    class Meta:
        model = App
        fields = "__all__"

    # add every new app to FULL ACCESS GROUP
    def clean_group(self):
        data = self.cleaned_data['group']
        AccessGroup.objects.get_or_create(group=AccessGroup.FULL)
        fag = AccessGroup.objects.filter(group=AccessGroup.FULL)
        data |= fag

        return data
