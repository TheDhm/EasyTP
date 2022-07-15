#!/bin/sh

set -e

python manage.py collectstatic
exec gunicorn --bind :8000 --workers 3 Docker2CS.wsgi
