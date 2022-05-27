echo "1- creating namespaces"
kubectl apply -f ./deploy-django/namespaces.yaml
echo " "

echo "2- creating persistent volumes and claims ( storage for users and teachers )"
kubectl apply -f ./deploy-django/persistentVolume.yaml
echo " "

echo "3- creating Service account ( for django app )"
kubectl apply -f ./deploy-django/ServiceAccount.yaml
echo " "

echo "4- creating Roles for the service account"
kubectl apply -f ./deploy-django/Role.yaml
echo " "

echo "5- creating Role Bindings between role and service account"
kubectl apply -f ./deploy-django/RoleBinding.yaml
echo " "

echo "6- creating Postgres secrets"
kubectl apply -f ./deploy-django/postgres/postgres-secrets.yaml
echo " "

echo "7- creating Postgres persistent volume and claim ( nfs_share/DB )"
kubectl apply -f ./deploy-django/postgres/postgres-pv.yaml
echo " "

echo "8- creating Postgres deployment"
kubectl apply -f ./deploy-django/postgres/postgres-deployment.yaml
echo " "

echo "9- creating Postgres service"
kubectl apply -f ./deploy-django/postgres/postgres-service.yaml
echo " "

echo "10- creating Django app deployment"
kubectl apply -f ./deploy-django/django-deployment.yaml
echo " "

echo "11- creating Django app service"
kubectl apply -f ./deploy-django/ServiceDjango.yaml
echo " "

echo "migrate and create super user and everything is done"
#### migrations to DB ####
# kubectl -n django-space exec -it  <django pod> -- python manage.py migrate
### creating super user
# kubectl -n django-space exec -it  <django pod> -- python manage.py createsuperuser











