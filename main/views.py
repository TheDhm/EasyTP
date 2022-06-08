import uuid
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.conf import settings
from .models import Pod, App, DefaultUser, AccessGroup, Instances
import hashlib
from .custom_functions import autotask
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException
import os
import base64
from .forms import UploadFileForm
import mimetypes

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
    except ConfigException:
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
def deploy_app(pod_name, app_name, image, vnc_password, user_hostname, readonly=False, *args, **kwargs):
    try:
        config.load_kube_config()
    except ConfigException:
        config.load_incluster_config()

    apps_api = client.AppsV1Api()
    user_space = user_hostname

    user_hostname = user_hostname.replace('_', '-')  # " _ " not allowed in kubernetes hostname

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
                    "hostname": user_hostname,
                    # "securityContext": {
                    #     "runAsUser": 1000
                    # },
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
                                },
                                {
                                    "name": "USER_HOSTNAME",
                                    "value": user_hostname
                                }
                            ],
                            "volumeMounts": [
                                {
                                    "name": "nfs-kube",
                                    "mountPath": "/data/myData",
                                    # "subPath": app_name + "/" + pod_name
                                    "subPath": user_space
                                },
                                {
                                    "name": "nfs-kube-readonly",
                                    "mountPath": "/data/readonly",
                                    "readOnly": readonly,
                                }
                            ]

                        }
                    ],
                    "volumes": [
                        {
                            "name": "nfs-kube",
                            "nfs":
                                {
                                    "server": "192.168.0.196",
                                    "path": "/mnt/nfs_share/USERDATA"
                                }
                        },
                        {
                            "name": "nfs-kube-readonly",
                            "nfs":
                                {
                                    "server": "192.168.0.196",
                                    "path": "/mnt/nfs_share/READONLY"
                                }
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


def start_pod(request, app_name, user_id=None):
    if request.user.is_authenticated:
        try:
            user_id = int(user_id)
        except:
            user_id = None

        readonly_volume = False
        user = request.user

        if request.user.role != DefaultUser.STUDENT:
            if user_id:
                try:
                    user = DefaultUser.objects.get(id=user_id)
                except DefaultUser.DoesNotExist:
                    return redirect(request.META['HTTP_REFERER'])
        else:
            readonly_volume = True


        try:
            pod = Pod.objects.get(pod_user=user, app_name=app_name)
            app = App.objects.get(name=app_name)
        except (App.DoesNotExist, Pod.DoesNotExist):
            return redirect(request.META['HTTP_REFERER'])

        deploy_app(pod_name=pod.pod_name,
                   app_name=app_name.lower(),
                   image=app.image,
                   vnc_password=hashlib.md5(pod.pod_vnc_password.encode("utf-8")).hexdigest(),
                   user_hostname=user.username,
                   readonly=readonly_volume)

        create_service(pod_name=pod.pod_name, app_name=app_name.lower())

        new_instance = Instances.objects.get_or_create(pod=pod, instance_name=pod.pod_name)

    return redirect(request.META['HTTP_REFERER'])


def stop_pod(request, app_name, user_id=None):
    if request.user.is_authenticated:
        try:
            user_id = int(user_id)
        except:
            user_id = None

        if user_id and request.user.role != DefaultUser.STUDENT:
            try:
                user = DefaultUser.objects.get(id=user_id)
            except DefaultUser.DoesNotExist:
                return redirect(request.META['HTTP_REFERER'])
        else:
            user = request.user

        try:
            pod = Pod.objects.get(pod_user=user, app_name=app_name)
        except Pod.DoesNotExist:
            return redirect(request.META['HTTP_REFERER'])

        pod_name = pod.pod_name

        try:
            config.load_kube_config()
        except ConfigException:
            config.load_incluster_config()

        api_instance = client.CoreV1Api()
        apps_instance = client.AppsV1Api()
        app_name = app_name.lower()

        try:
            deleted_service = api_instance.delete_namespaced_service(namespace="apps",
                                                                     name=app_name + "-service-" + pod_name)
        except ApiException as a:
            print("delete service exception", a)

        try:
            deleted_deployment = apps_instance.delete_namespaced_deployment(namespace="apps",
                                                                            name=app_name + "-deployment-" + pod_name)
        except ApiException as a:
            print("delete deployment exception", a)

        try:
            instance = Instances.objects.get(pod=pod, instance_name=pod_name)
            instance.delete()

        except Instances.DoesNotExist as e:
            print("instance already deleted", e)

    return redirect(request.META['HTTP_REFERER'])


def display_apps(apps, user):
    data = dict()
    for app in apps:
        status = False
        port = None
        ip = None

        try:
            pod = Pod.objects.get(pod_user=user, app_name=app.name)
        except Pod.DoesNotExist:
            pod = None

        if pod:
            vnc_pass = pod.pod_vnc_password
            pod_name = pod.pod_name

        else:  # create pod if not exist --> case where admin add new apps after user created
            pod_name = hashlib.md5(
                f'{app.name}:{user.username}:{user.id}'.encode("utf-8")).hexdigest()
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
            except ConfigException:
                config.load_incluster_config()

            api_instance = client.CoreV1Api()
            apps_instance = client.AppsV1Api()

            service = api_instance.list_namespaced_service(namespace="apps",
                                                           label_selector="serviceApp={}".format(pod_name))
            deployment = apps_instance.list_namespaced_deployment(namespace="apps",
                                                                  label_selector="deploymentApp={}".format(
                                                                      pod_name))
            pod = api_instance.list_namespaced_pod(namespace="apps",
                                                   label_selector="appDep={}".format(pod_name))

            if len(service.items) != 0:
                if len(deployment.items) != 0:
                    if deployment.items[0].status.ready_replicas:
                        status = True
                        port = service.items[0].spec.ports[0].node_port
                        # port = service.items[0].spec.ports[0].port
                        ip = pod.items[0].status.host_ip
                        # ip = service.items[0].spec.cluster_ip
                    else:
                        print("no replicas ready")
                else:
                    print("no deployment found")
            else:
                print("service ", app, " is down")

        except Exception as e:
            print("#DEBUG:deployment status error handling")
            print(e)
        data[app.name] = dict(
            {"vnc_pass": vnc_pass, "deployment_status": status, "ip": ip, "port": port})

    return data


def test_apps(request):
    data = dict()
    if request.user.is_authenticated:
        if request.user.role == DefaultUser.TEACHER or request.user.role == DefaultUser.ADMIN:
            apps = App.objects.all()
            data = display_apps(apps, request.user)

        else:
            user = request.user
            apps = user.group.apps.all()
            data = display_apps(apps, user)

    return render(request, 'main/display_apps.html', {"data": data})


def homepage(request):
    data = dict()
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.role == DefaultUser.ADMIN:
            return render(request, 'main/admin.html')

        elif request.user.role == DefaultUser.TEACHER:
            return render(request, 'main/teacher_home.html')

        elif request.user.role == DefaultUser.STUDENT:
            return render(request, 'main/student_home.html')

    return render(request, 'main/display_apps.html')


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

    return render(request, "main/login.html", {"form": form})


def list_students(request, group_id=None, app_id=None):
    if request.user.is_authenticated:
        user = request.user
        if user.role == DefaultUser.TEACHER:
            teacher = user
            groups = AccessGroup.objects.exclude(name__exact=AccessGroup.FULL)
            apps_to_template = []
            current_group = None
            current_app = None

            data = dict()

            try:
                group_id = int(group_id)
            except:
                group_id = None

            if group_id and group_id != AccessGroup.FULL:

                try:
                    group = AccessGroup.objects.get(id=group_id)
                    students = group.students.filter(role__exact=DefaultUser.STUDENT)
                    apps = group.apps.all()
                    current_group = group

                except AccessGroup.DoesNotExist:
                    students = None
                    apps = None

                apps_to_template = apps

                try:
                    app_id = int(app_id)
                except:
                    app_id = None

                if app_id:
                    try:
                        app = App.objects.get(id=app_id)
                    except App.DoesNotExist:
                        app = None

                    if app:
                        data[app.name] = []
                        current_app = app
                        for student in students:
                            instance = None
                            deployment_status = False
                            try:
                                pod = Pod.objects.get(pod_user=student, app_name=app.name)
                            except Pod.DoesNotExist:
                                pod = None
                            #
                            # if pod:
                            #     try:
                            #         instance = Instances.objects.get(pod=pod, instance_name=pod.pod_name)
                            #     except Instances.DoesNotExist:
                            #         instance = None
                            # if pod and instance:
                            #     deployment_status = True

                            data[app.name].append({'info': student,
                                                   **display_apps([app], student)[app.name]})

            return render(request, 'main/list_students.html', {'data': data,
                                                               'groups': groups,
                                                               'apps': apps_to_template,
                                                               'current_group': current_group,
                                                               'current_app': current_app})

    return render(request, 'main/display_apps.html')


# def direct_connect(request, app=None, user_id=None):
#     if request.user.is_authenticated:
#         if request.user.role == DefaultUser.TEACHER:
#             if app and user_id:


def get_sub_files(root_path, path):
    subfiles = {}

    directory = os.path.join(root_path, path)
    try:
        files_list = os.listdir(directory)
    except FileNotFoundError:
        os.mkdir(directory)
        files_list = os.listdir(directory)

    files_list.sort()

    for file in files_list:
        path = os.path.join(directory, file)
        subfiles[file] = {'is_dir': os.path.isdir(path),
                          'path': base64.urlsafe_b64encode(bytes(path.split(root_path)[1], encoding='utf8')).decode()}

    return subfiles


@autotask
def save_file(path, file):
    with open(os.path.join(path, file.name), 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def file_explorer(request, path=None):
    if request.user.is_authenticated:
        if request.user.role != DefaultUser.STUDENT:  # if not student => teacher or admin
            # open read only folder:

            # _readonly
            # |__LOGISIM
            # |  |__ tp files
            # |__GNS3
            #    |__ tp files

            # user_path = '/mnt/nfs_share/readonly/'
            user_path = '/READONLY/'

        else:  # user is student

            # user_path = '/mnt/nfs_share/USERDATA/' + request.user.username + '/'
            user_path = '/USERDATA/' + request.user.username + '/'

        if path:
            path = base64.urlsafe_b64decode(path).decode()
            path = path.split('..')[0]  # Critical : escape /../

            current_path = 'myspace/' + path
            parent = '/'.join(path.split('/')[:-2])
            parent_path_encoded = base64.urlsafe_b64encode(bytes(parent, encoding='utf8')).decode()

        else:
            current_path = 'myspace/'
            path = ''
            parent_path_encoded = ''

        sub_files = get_sub_files(user_path, path)

        if request.method == 'POST':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                file_size = file.size / 1048576

                if file_size + request.user.upload_limit <= 1024:

                    save_to = os.path.join(user_path, path)
                    save_file(save_to, file)
                    request.user.upload_limit += file_size
                    request.user.save()

        else:
            form = UploadFileForm()

        return render(request, 'main/file_explorer.html', {'data': sub_files,
                                                           'current_path': current_path,
                                                           'parent_path_encoded': parent_path_encoded,
                                                           'form': form})


def download_file(request, path):
    if request.user.is_authenticated:
        user = request.user

        path = base64.urlsafe_b64decode(path).decode()
        path = path.split('..')[0]  # Critical : escape /../
        file_name = path.split('/')[-1]

        if user.role == DefaultUser.STUDENT:
            # user_space = os.path.join('/mnt/nfs_share/USERDATA/', user.username)
            user_space = os.path.join('/USERDATA/', user.username)

        else:
            # user_space = os.path.join('/mnt/nfs_share/readonly/', )
            user_space = os.path.join('/READONLY/', )

        full_path = os.path.join(user_space, path)
        mime_type, _ = mimetypes.guess_type(full_path)

        file = open(full_path, 'rb')
        response = HttpResponse(file, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % file_name

        return response
