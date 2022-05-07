# Container Manager App

## About 
## Built with
* Django
* Docker 
* Kubernetes 
## Structure
### Modules
### 
## Getting started
These instruction will get you a copy of this project up running on your local machine .

### Prerequisites

* Docker
* Python 3 *(you can get it from [here](https://www.python.org/downloads/))*
* virtualenv 
```sh
pip install virtualenv
```
### Create a virtual environement

```sh
virtualenv "Your virtualenv name"  
cd "Your virtualenv name"
Scripts\activate
```
### Installation
1. Clone the repo
```sh
git clone https://github.com/TheDhm/container-manager-app.git
```
2. Install required packages
```sh
pip install -r requirements.txt
```
3. Before you start the project make sur to have these docker images locally :
* [Gns3](https://hub.docker.com/r/younes46/gns)
```sh 
docker pull younes46/gns
docker tag younes46/gns gns3
```
* [Logisim](https://hub.docker.com/repository/docker/anii76/logisim)
```sh 
docker pull anii76/logisim
docker tag anii76/logisim logisim
```
### Or
Build the dockerfiles in `Dockerfiles`
```sh 
docker build -t <ImageName> <DockerfilePath>
```
4. Change the directory for container volumes *(Persistant data)* in `Docker2CS/settings.py` to another path in your machine:
```sh
PARENT_DIR = "/home/zulu/userdata"
```
5. Make migrations & migrate
```sh
python manage.py makemigrations
python manage.py migrate
```
6. Create super user *(use @esi.dz email address)*
```sh
python manage.py createsuperuser
```
7. Run server 
```sh
python manage.py runserver
```

## Usage
## Contributing
## License
## Contact

