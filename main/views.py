from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from threading import Thread
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.conf import settings
from .models import Containers, Instances
import docker
import hashlib
import os
from .forms import AddUsersCSV

app_name = "main"


def autotask(func):
    def decor(*args, **kwargs):
        t = Thread(target=func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

    return decor


@autotask
def run_docker(app_name, port, container_name, vnc_password, path, *args, **kwargs,):
    client = docker.from_env()
    try:
        container = client.containers.run(image=settings.DEFAULT_APP_LIST[app_name],
                                          detach=True,
                                          ports={'8080': int(port)},
                                          name=container_name,
                                          volumes=[f'{path}:/data'],
                                          environment=[f"VNC_PW={vnc_password}", "VNC_RESOLUTION=1366x768"])
        print("### run docker ### " + container_name)
    except Exception as e:
        print("#DEBUG:EXCEPTION IN run_docker")
        print(e)  # Handle exception and log it here
        try:
            container = client.containers.get(container_name)
            container.start()
        except Exception as e:
            print("#DEBUG:EXCEPTION IN run_docker : container.get()")
            print(e)  # Handle exception and log it here
    return


def add_from_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES["csv_file"]
        form = AddUsersCSV(request.POST, request.FILES)
        if not csv_file.name.endswith('.csv'):
            messages.warning(request, 'The wrong file type was uploaded')
            return HttpResponseRedirect(request.path_info, {'form': form})

        if form.is_valid():
            # TODO
            messages.success(request, 'Users created !')
            url = reverse('admin:main_defaultuser_changelist')

            return HttpResponseRedirect(url)
    else:
        form = AddUsersCSV()
    data = {'form': form}
    return render(request, "admin/add_from_csv.html", context=data)


def homepage(request):
    data = dict()
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return render(request, 'main/admin.html')

        containers = request.user.container_user.all()
        for container in containers:
            status = False
            container_app = container.app_name
            vnc_pass = container.container_vnc_password
            vnc_pass = hashlib.md5(vnc_pass.encode("utf-8")).hexdigest()

            try:
                client = docker.from_env()
                docker_container = client.containers.get(container.container_name)
                status = docker_container.attrs["State"]["Running"]
            except Exception as e:
                print("#DEBUG:Container status error handling")
                print(e)
                pass
            data[container_app] = dict(
                {"vnc_pass": vnc_pass, "container_status": status, "port": container.container_port})
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

                return redirect("main:homepage")
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe invalide(s) !")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe invalide(s) !")
    form = AuthenticationForm

    return render(request,
                  "main/login.html",
                  {"form": form})


def start_container(request, app):
    if request.user.is_authenticated:
        if not request.user.is_superuser and not request.user.is_staff:
            container = Containers.objects.get(container_user=request.user, app_name=app)

            run_docker(app_name=container.app_name,
                       port=container.container_port,
                       container_name=container.container_name,
                       vnc_password=hashlib.md5(container.container_vnc_password.encode("utf-8")).hexdigest(),
                       path=os.path.join(settings.PARENT_DIR, hashlib.md5(f'{request.user.id}'.encode("utf-8")).hexdigest())
                       )
            # TODO : vulnerability, args should be generated dynamically to avoid injection ( port & container_name )
            new_instance = Instances.objects.get_or_create(container=container, instance_name=f'{container.app_name}')

    return redirect("main:homepage")


def stop_container(request, app):
    if request.user.is_authenticated:
        client = docker.from_env()
        container_name = request.user.container_user.get(app_name=app).container_name
        container = client.containers.get(container_name)
        container.stop()

    return redirect("main:homepage")


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
