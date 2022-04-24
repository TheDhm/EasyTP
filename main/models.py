from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
import hashlib
import uuid
import os


class Containers(models.Model):
    container_user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, related_name="container_user")
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


@receiver(post_save, sender=User)
def generateContainer(sender, instance, created, **kwargs):
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
                    container_name=hashlib.md5(f'{app}:{instance.username}:{instance.id}'.encode("utf-8")).hexdigest(),
                    container_port=settings.DEFAULT_APP_PORT_RANGE+str(instance.id*n_of_apps-port_calculator).zfill(4),
                    container_vnc_user=uuid.uuid4().hex[:6],
                    container_vnc_password=uuid.uuid4().hex
                      )
            model.save()
            port_calculator += 1
