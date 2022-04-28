from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
import hashlib
import uuid
import os
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .custom_validators import EsiEmailValidator, validate_year


class DefaultUser(AbstractUser):
    email = models.EmailField(_('email address'),
                              max_length=50,
                              blank=False,
                              unique=True,
                              help_text=_('Enter the email of the user, must ends with @esi.dz'),
                              validators=[EsiEmailValidator(allowlist=['esi.dz'],
                                                            message='Enter a valid "@esi.dz" email address.')])

    T = 'T'
    S = 'S'
    Admin = 'A'
    ROLES = [
        (T, 'Teacher'),
        (S, 'Student'),
        (Admin, 'Staff'),
    ]
    role = models.CharField(max_length=1, choices=ROLES, default=T, blank=False)

    CP1 = '1cp'
    CP2 = '2cp'
    CS1 = '1CS'
    CS2 = '2CS'

    YEARS = [
        (CP1, 'Cycle Préparatoire 1'),
        (CP2, 'Cycle Préparatoire 2'),
        (CS1, 'Second Cycle 1'),
        (CS2, 'Second Cycle 2'),
    ]
    year = models.CharField(max_length=3, choices=YEARS, default=CP1, blank=True)

    def save(self, *args, **kwargs):
        self.username = self.email.split('@esi.dz')[0]

        if self.role == self.Admin:
            self.is_staff = True
        if self.role != self.S:
            self.year = ''
        super().save(*args, **kwargs)


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
