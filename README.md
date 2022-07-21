# Container Manager App

## About 
This project consists of modernizing (Containerization) of applications used by ESI students and implementation of a custom onsite Kubernetes cluster architecture to deploy and manage student access and activity.

## Built with
* Django
* Docker 
* Kubernetes 
## Structure
### Modules
### 
## Getting started
These instructions will get you a copy of this project up running on your local machine .

### Prerequisites
* Docker
* cri-dockerd *(you can get it from [here](https://github.com/Mirantis/cri-dockerd))*
* Kubernetes (you can follow this [tutorial](https://phoenixnap.com/kb/install-kubernetes-on-ubuntu) to install kubeadm, kubelet and kubectl)

[//]: # (* Python 3 *&#40;you can get it from [here]&#40;https://www.python.org/downloads/&#41;&#41;*)

[//]: # (* virtualenv)

[//]: # (```sh)

[//]: # (pip install virtualenv)

[//]: # (```)

[//]: # (### Create a virtual environement)

[//]: # ()
[//]: # (```sh)

[//]: # (virtualenv "Your virtualenv name"  )

[//]: # (cd "Your virtualenv name")

[//]: # (Scripts\activate)

[//]: # (```)

### Installation
1. Create your cluster
```sh
swapoff -a
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --cri-socket=unix:///var/run/cri-dockerd.sock --apiserver-advertise-address=<your ip>

mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
# install flannel: network plugin
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
# enable scheduling on master
kubectl taint node --all node-role.kubernetes.io/master:NoSchedule-
kubectl taint node --all node-role.kubernetes.io/control-plane:NoSchedule-
```
2. Clone the repo
```sh
git clone https://github.com/TheDhm/container-manager-app.git
```
3. Create NFS storage (you can follow this [tutorial](https://www.tecmint.com/install-nfs-server-on-ubuntu/))
    * create DB folder in your nfs server (for postgres DB)
    * create USERDATA folder ( users storage space )
    * create READONLY folder
    * make sure to change nfs server IP in: 
      * postgres-pv.yaml
      * django-deployment.yaml
      * persistentVolume.yaml


4. Build the web app image
```sh
cd container-manager-app
docker build --rm -t django-app:latest .
```
5. Before you start the project make sur you have docker images locally :

[//]: # (* [Gns3]&#40;https://hub.docker.com/r/younes46/gns&#41;)

[//]: # (```sh )

[//]: # (docker pull younes46/gns)

[//]: # (docker tag younes46/gns gns3)

[//]: # (```)

[//]: # (* [Logisim]&#40;https://hub.docker.com/repository/docker/anii76/logisim&#41;)

[//]: # (```sh )

[//]: # (docker pull anii76/logisim)

[//]: # (docker tag anii76/logisim logisim)

[//]: # (```)

[//]: # (### Or)
you can build the images using dockerfiles in `Dockerfiles` (Logisim & GNS3)
```sh 
docker build -t <ImageName> <DockerfilePath>
```
6. Deploy on Kubernetes cluster
```sh
cd container-manager-app
sh deploy-all.sh
```
7. Migrate
```sh
kubectl -n django-space exec -it  <django pod> -- python manage.py migrate
```
8. Create superuser
```sh
kubectl -n django-space exec -it  <django pod> -- python manage.py createsuperuser
```

## Usage
## Contributing
## License
## Contact

