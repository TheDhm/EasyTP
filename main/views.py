import uuid
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.conf import settings
from .models import Pod, App
import hashlib
from .custom_functions import autotask
from kubernetes import client, config
from kubernetes.client.rest import ApiException

app_name = "main"


@autotask
def generate_pod_if_not_exist(pod_user, app_name, pod_name, pod_vnc_user, pod_vnc_password):
    pod = Pod(pod_user=pod_user,
              pod_name=pod_name,
              app_name=app_name,
              pod_vnc_user=pod_vnc_user,
              pod_vnc_password=pod_vnc_password,
              pod_namespace="apps")
    pod.save()


@autotask
def create_service(pod_name, app_name):
    try:
        config.load_kube_config()
    except ApiException:
        config.load_incluster_config()

    api_instance = client.CoreV1Api()

    manifest = {
        "kind": "Service",
        "apiVersion": "v1",
        "metadata": {
            "name": app_name + "-service-" + pod_name,
            "labels": {"serviceApp": pod_name}
        },
        "spec": {
            "selector": {
                "appDep": pod_name
            },
            "ports": [
                {
                    "protocol": "TCP",
                    "port": 8080,
                    "targetPort": 8080,
                }
            ],
            "type": "NodePort"
        }
    }

    try:
        api_response = api_instance.create_namespaced_service(namespace='apps', body=manifest, pretty='true')
    except ApiException as e:
        print("Exception when calling CoreV1Api->create_namespaced_endpoints: %s\n" % e)


@autotask
def deploy_app(pod_name, app_name, image, vnc_password, *args, **kwargs):
    try:
        config.load_kube_config()
    except ApiException:
        config.load_incluster_config()

    apps_api = client.AppsV1Api()

    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": app_name + "-deployment-" + pod_name,
            "labels": {
                "deploymentApp": pod_name
            }

        },
        "spec": {
            "selector": {
                "matchLabels": {
                    "app": app_name
                },
            },
            "replicas": 1,
            "template": {
                "metadata": {
                    "labels": {
                        "app": app_name,
                        "appDep": pod_name
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": app_name,
                            "image": image,
                            "imagePullPolicy": "Never",
                            "ports": [
                                {
                                    "containerPort": 8080
                                }
                            ],
                            "env": [
                                {
                                    "name": "VNC_PW",
                                    "value": vnc_password
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
    try:
        apps_api.create_namespaced_deployment(namespace="apps", body=deployment)
    except ApiException as e:
        print("error while deploying: ", e)


def start_pod(request, app_name):
    if request.user.is_authenticated:
        pod = Pod.objects.get(pod_user=request.user, app_name=app_name)
        app = App.objects.get(name=app_name)
        # print(hashlib.md5(pod.pod_vnc_password.encode("utf-8")).hexdigest())

        deploy_app(pod_name=pod.pod_name,
                   app_name=app_name.lower(),
                   image=app.image,
                   vnc_password=hashlib.md5(pod.pod_vnc_password.encode("utf-8")).hexdigest())

        create_service(pod_name=pod.pod_name, app_name=app_name.lower())
    return redirect("main:homepage")


def stop_pod(request, app_name):
    if request.user.is_authenticated:
        pod = Pod.objects.get(pod_user=request.user, app_name=app_name)
        pod_name = pod.pod_name

        try:
            config.load_kube_config()
        except ApiException:
            config.load_incluster_config()

        api_instance = client.CoreV1Api()
        apps_instance = client.AppsV1Api()
        app_name = app_name.lower()

        try:
            deleted_service = api_instance.delete_namespaced_service(namespace="apps",
                                                                     name=app_name + "-service-" + pod_name)

            deleted_deployment = apps_instance.delete_namespaced_deployment(namespace="apps",
                                                                            name=app_name + "-deployment-" + pod_name)
        except ApiException as a:
            print("delete exception", a)

    return redirect("main:homepage")


def homepage(request):
    data = dict()
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return render(request, 'main/admin.html')
        user = request.user
        apps = user.group.apps.all()

        for app in apps:
            status = False
            port = None
            ip = None

            try:
                pod = Pod.objects.get(pod_user=request.user, app_name=app.name)
            except Pod.DoesNotExist:
                pod = None

            if pod:
                vnc_pass = pod.pod_vnc_password
                pod_name = pod.pod_name

            else:  # create pod if not exist --> case where admin add new apps after user created
                pod_name = hashlib.md5(
                    f'{app_name}:{user.username}:{user.id}'.encode("utf-8")).hexdigest()
                pod_vnc_user = uuid.uuid4().hex[:6]
                pod_vnc_password = uuid.uuid4().hex
                generate_pod_if_not_exist(pod_user=user,
                                          pod_name=pod_name,
                                          app_name=app.name,
                                          pod_vnc_user=pod_vnc_user,
                                          pod_vnc_password=pod_vnc_password
                                          )
                vnc_pass = pod_vnc_password

            vnc_pass = hashlib.md5(vnc_pass.encode("utf-8")).hexdigest()

            try:
                try:
                    config.load_kube_config()
                except ApiException:
                    config.load_incluster_config()

                api_instance = client.CoreV1Api()
                apps_instance = client.AppsV1Api()

                service = api_instance.list_namespaced_service(namespace="apps",
                                                               label_selector="serviceApp={}".format(pod_name))
                deployment = apps_instance.list_namespaced_deployment(namespace="apps",
                                                                      label_selector="deploymentApp={}".format(
                                                                          pod_name))

                if len(service.items) != 0:
                    if len(deployment.items) != 0:
                        if deployment.items[0].status.ready_replicas:
                            status = True
                            # port = service.items[0].spec.ports[0].node_port
                            port = service.items[0].spec.ports[0].port
                            ip = service.items[0].spec.cluster_ip
                        else:
                            print("no replicas ready")
                    else:
                        print("no deployment found")
                else:
                    print("service is down")

            except Exception as e:
                print("#DEBUG:deployment status error handling")
                print(e)
            data[app] = dict(
                {"vnc_pass": vnc_pass, "deployment_status": status, "ip": ip, "port": port})
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
