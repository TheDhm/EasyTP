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
        AccessGroup.objects.get_or_create(name=AccessGroup.FULL)
        fag = AccessGroup.objects.filter(name=AccessGroup.FULL)
        data |= fag

        return data


class CustomChangeAccessGroup(forms.ModelForm):
    apps = forms.ModelMultipleChoiceField(queryset=App.objects.all(), required=True,
                                          help_text='Choose which apps to give access to',
                                          widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super(CustomChangeAccessGroup, self).__init__(*args, **kwargs)
        group = kwargs['instance']
        self.fields['apps'].initial = [app for app in group.apps.all()]

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
    name = forms.ChoiceField(choices=[('add_new', 'ADD New')] + AccessGroup.GROUPS,
                             label="Legacy access groups",
                             help_text='choose legacy group from list')
    add_new = forms.CharField(max_length=25, required=False,
                              help_text='to add a new group select ADD NEW in legacy group',
                              label='Add new group')

    apps = forms.ModelMultipleChoiceField(queryset=App.objects.all(), required=False,
                                          help_text='Choose which apps to give access to',
                                          widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        data = args[0] if args else kwargs.get('data', None)
        super(CustomAddAccessGroup, self).__init__(*args, **kwargs)
        if data:
            if data['add_new'] and data['name'] == 'add_new':
                _mutable = data._mutable
                data._mutable = True
                data['name'] = data['other']
                data._mutable = _mutable

                self.fields['name'].choices += [(data['other'], data['other'])]

    def save(self, commit=True):
        instance = super().save(commit=False)

        apps = self.cleaned_data['apps']

        instance.save()
        instance.apps.set(apps)

        return instance

    class Meta:
        model = AccessGroup
        fields = "__all__"
