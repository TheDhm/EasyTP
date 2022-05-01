from django.core.validators import FileExtensionValidator
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
import hashlib
import uuid
import os
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .custom_validators import EsiEmailValidator, validate_emails_in_file
from pandas import read_csv, read_excel
from django.contrib.auth.hashers import make_password


class AccessGroup(models.Model):
    CP1 = '1CP'
    CP2 = '2CP'
    CS1 = '1CS'
    CS2 = '2CS'
    FULL = 'FUL'

    GROUPS = [
        (FULL, 'Full Access Group'),
        (CP1, 'Cycle Préparatoire 1'),
        (CP2, 'Cycle Préparatoire 2'),
        (CS1, 'Second Cycle 1'),
        (CS2, 'Second Cycle 2'),
    ]

    group = models.CharField(max_length=3, choices=GROUPS, default=CP1, unique=True, blank=False)

    def __str__(self):
        return f'{self.get_group_display()}'

    def has_access_to(self):
        return ", ".join([a.name for a in self.apps.all()])


class App(models.Model):
    name = models.CharField(max_length=50, blank=False, unique=True)
    group = models.ManyToManyField(AccessGroup, related_name='apps', blank=True)
    images = models.CharField(max_length=10)

    def __str__(self):
        return f'{self.name}'

    def groups(self):
        return ", ".join([g.get_group_display() for g in self.group.all()])


class DefaultUser(AbstractUser):
    email = models.EmailField(_('email address'),
                              max_length=50,
                              blank=False,
                              unique=True,
                              help_text=_('Enter the email of the user, must ends with @esi.dz'),
                              validators=[EsiEmailValidator(allowlist=['esi.dz'],
                                                            message='Enter a valid "@esi.dz" email address.')],
                              )

    TEACHER = 'T'
    STUDENT = 'S'
    ADMIN = 'A'
    ROLES = [
        (TEACHER, 'Teacher'),
        (STUDENT, 'Student'),
        (ADMIN, 'Staff'),
    ]
    role = models.CharField(max_length=1, choices=ROLES, default=ADMIN, blank=False)

    def save(self, *args, **kwargs):
        self.username = self.email.split('@esi.dz')[0]

        if self.role == self.ADMIN or self.is_superuser:
            self.is_staff = True

        # add superusers,staff and teachers to FULL ACCESS GROUP
        if self.role != self.STUDENT:
            self.group = AccessGroup.objects.get_or_create(group=AccessGroup.FULL)[0]

        super().save(*args, **kwargs)

    group = models.ForeignKey(AccessGroup, on_delete=models.SET_DEFAULT, default=None, null=True)

    def apps_available(self):
        if not self.group:
            return f'Not in a group yet'
        return self.group.has_access_to()


class Containers(models.Model):
    container_user = models.ForeignKey(DefaultUser, on_delete=models.CASCADE, default=None,
                                       related_name="container_user")
    app_name = models.CharField(max_length=200, default=None, blank=False, null=True)
    container_name = models.CharField(max_length=200, default=None, blank=False, null=True)
    container_port = models.CharField(max_length=200, default=None, blank=False, null=True)
    container_vnc_user = models.CharField(max_length=200, default=None, blank=False, null=True)
    container_vnc_password = models.CharField(max_length=200, default=None, blank=False, null=True)

    date_created = models.DateTimeField(auto_now_add=True, blank=True)
    date_modified = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return f'{self.container_user.username}:{self.container_name}:{self.container_port}'


class Instances(models.Model):
    container = models.OneToOneField(Containers, on_delete=models.CASCADE, default=None, related_name="container")
    instance_name = models.CharField(max_length=200, default=None, blank=False, null=True)
    date_created = models.DateTimeField(auto_now_add=True, blank=True)
    date_modified = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return f'{self.container}:{self.instance_name}'


class UsersFromCSV(models.Model):
    file = models.FileField(default='',
                            validators=[FileExtensionValidator(['csv', 'xlsx'])])
                                        # validate_emails_in_file],
                            # )  # TODO : fix emails validator

    role = models.CharField(max_length=1, choices=DefaultUser.ROLES, default=DefaultUser.STUDENT, blank=False)
    group = models.ForeignKey(AccessGroup, on_delete=models.SET_DEFAULT, default=None)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if str(self.file).endswith('.csv'):
            users = read_csv(self.file)
        else:
            users = read_excel(self.file)

        for email in users.iloc[:, 0]:
            user_exist = DefaultUser.objects.filter(email=email)
            if user_exist:
                try:
                    user_exist.update(email=email,
                                      password=make_password(email.split("@")[0]),
                                      role=self.role,
                                      group=self.group,
                                      username=email.split("@")[0]
                                      )
                except Exception as e:
                    print("user ", email, " not updated")
                    print(e)
            else:
                try:
                    user = DefaultUser.objects.create_user(email=email,
                                                           password=make_password(email.split("@")[0]),
                                                           role=self.role,
                                                           group=self.group,
                                                           username=email.split("@")[0]
                                                           )

                except Exception as e:
                    print("user ", email, "not created")
                    print(e)

    def __str__(self):
        return self.role + 's'


@receiver(post_save, sender=DefaultUser)
def generate_container(sender, instance, created, **kwargs):
    if created:
        port_calculator = 0
        n_of_apps = len(settings.DEFAULT_APP_NAME)
        # create dir for user
        user_directory = hashlib.md5(f'{instance.id}'.encode("utf-8")).hexdigest()
        path = os.path.join(settings.PARENT_DIR, user_directory)
        try:
            os.mkdir(path)
        except OSError as error:
            print(error)

        for app in settings.DEFAULT_APP_NAME:
            # app_name = settings.DEFAULT_APP_LIST[app]
            model = Containers(container_user=instance,
                               app_name=app,
                               container_name=hashlib.md5(
                                   f'{app}:{instance.username}:{instance.id}'.encode("utf-8")).hexdigest(),
                               container_port=settings.DEFAULT_APP_PORT_RANGE + str(
                                   instance.id * n_of_apps - port_calculator).zfill(4),
                               container_vnc_user=uuid.uuid4().hex[:6],
                               container_vnc_password=uuid.uuid4().hex
                               )
            model.save()
            port_calculator += 1
