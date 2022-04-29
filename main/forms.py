from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import DefaultUser, AccessGroup, App
from django.core.validators import FileExtensionValidator


class AddUsersCSV(forms.Form):
    csv_file = forms.FileField(label='csv file',
                               max_length=200,
                               allow_empty_file=False,
                               required=True,
                               validators=[FileExtensionValidator(['csv', ''])])
    role = forms.ChoiceField(label='choose role for users', choices=DefaultUser.ROLES, required=True)
    group = forms.ChoiceField(label='choose group for users', choices=AccessGroup.GROUPS, required=False)


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
        print(data)
        AccessGroup.objects.get_or_create(group='FUL')
        fag = AccessGroup.objects.filter(group='FUL')
        data |= fag

        return data
