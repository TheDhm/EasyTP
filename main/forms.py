from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import DefaultUser, AccessGroup, App, UsersFromCSV
from django.core.validators import FileExtensionValidator


class UsersFromCSVForm(forms.ModelForm):
    class Meta:
        model = UsersFromCSV
        fields = "__all__"
        help_texts = {
            'file': 'Upload a CSV (or excel) file containing emails of new users, emails must end with "@esi.dz"',
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
        widgets = {"group": forms.CheckboxSelectMultiple}

    # add every new app to FULL ACCESS GROUP
    def clean_group(self):
        data = self.cleaned_data['group']
        AccessGroup.objects.get_or_create(group=AccessGroup.FULL)
        fag = AccessGroup.objects.filter(group=AccessGroup.FULL)
        data |= fag

        return data


class CustomChangeAccessGroup(forms.ModelForm):
    def get_group(self):
        return self.cleaned_data["group"]

    apps = forms.ModelMultipleChoiceField(queryset=App.objects.all(), required=True,
                                          help_text='Choose which apps to give access to',
                                          widget=forms.CheckboxSelectMultiple,
                                          initial=[])  # TODO

    def save(self, commit=True):
        instance = super().save(commit=False)

        apps = self.cleaned_data['apps']

        instance.save()
        instance.apps.set(apps)

        return instance

    class Meta:
        model = AccessGroup
        fields = "__all__"


class CustomAddAccessGroup(forms.ModelForm):

    group = forms.ChoiceField(choices=AccessGroup.GROUPS, label="Legacy access groups")
    other = forms.CharField(max_length=3, required=False,
                            help_text='ID of new group ,if specified it\'ll override group choice',
                            label='Add new group')
    description = forms.CharField(max_length=20, required=False,
                                  help_text='Description of the new group, required if new group specified')
    apps = forms.ModelMultipleChoiceField(queryset=App.objects.all(), required=True,
                                          help_text='Choose which apps to give access to',
                                          widget=forms.CheckboxSelectMultiple)

    def save(self, commit=True):
        if self.cleaned_data['other']:
            self.cleaned_data['group'] = self.cleaned_data['other']
        instance = super().save(commit=False)

        apps = self.cleaned_data['apps']

        instance.save()
        instance.apps.set(apps)

        return instance

    class Meta:
        model = AccessGroup
        fields = "__all__"
