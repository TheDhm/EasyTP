from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from threading import Thread
from time import sleep
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.conf import settings
from .models import Containers,Instances
import docker
import hashlib

app_name = "main"


def autotask(func):
    def decor(*args, **kwargs):
        t = Thread(target=func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decor


@autotask
def run_docker(app_name,port,container_name,vnc_password ,*args,**kwargs):
    client = docker.from_env()
    try:
        container = client.containers.run(image=settings.DEFAULT_APP_LIST[app_name],
                              detach=True,
                              ports={'8080':int(port)},
                              name=container_name,
                              environment=[f"VNC_PW={vnc_password}", "VNC_RESOLUTION=1366x768"])
        print("### run docker ### "+container_name)
    except Exception as e:
        print("#DEBUG:EXCEPTION IN run_docker")
        print(e)#Handle exception and log it here
        try:
            container = client.containers.get(container_name)
            container.start()
        except Exception as e:
            print("#DEBUG:EXCEPTION IN run_docker : container.get()")
            print(e)  # Handle exception and log it here
    return


def homepage(request):
    vnc_pass = False
    status = False
    data = dict()
    if request.user.is_authenticated:
        containers = request.user.container_user.all()
        for container in containers:
            container_app = container.app_name
            vnc_pass = container.container_vnc_password
            vnc_pass = hashlib.md5(vnc_pass.encode("utf-8")).hexdigest()

            try:
                client = docker.from_env()
                print("### home ### "+container.container_name)
                docker_container = client.containers.get(container.container_name)
                status = docker_container.attrs["State"]["Running"]
            except Exception as e:
                print("#DEBUG:Container status error handling")
                print(e)
                pass
            data[container_app] = dict({"vnc_pass": vnc_pass, "container_status": status, "port": container.container_port})
    print(data)
    return render(request,
                  "main/main.html",
                  {"data": data})


def logout_request(request):
    logout(request)
    return redirect("main:homepage")


def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            # noinspection PyStringFormat
            if user is not None:
                login(request, user)
                messages.info(request, f"Bienvenue, vous etes connecté !")
                if not user.is_superuser:
                    containers = Containers.objects.filter(container_user=user)
                    port_calculator = 0

                    for container in containers:

                        image_name = settings.DEFAULT_APP_LIST[container.app_name]
                        run_docker(app_name=container.app_name,
                               port=settings.DEFAULT_APP_PORT_RANGE+str(user.id*2-port_calculator).zfill(4),
                               container_name=hashlib.md5(f'{image_name}:{user.username}:{user.id}'.encode("utf-8")).hexdigest(),
                               vnc_password=hashlib.md5(container.container_vnc_password.encode("utf-8")).hexdigest()
                               )
                        port_calculator += 1
                        new_instance = Instances.objects.get_or_create(container=container, instance_name=f'{container.app_name}')
                return redirect("main:homepage")
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe invalide(s) !")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe invalide(s) !")
    form = AuthenticationForm

    return render(request,
                  "main/login.html",
                  {"form": form})


def watch_dog_notification(request):
    client = docker.from_env()
    instances = Instances.objects.all()
    actif_containers = []
    print("actif_containers", actif_containers)
    for container in client.containers.list():
        actif_containers.append(container.name)
    for instance in instances:
        print("Instance", instance.container.container_name)
        if instance.container.container_name not in actif_containers:
            instance.delete()
    return HttpResponse("OK")


