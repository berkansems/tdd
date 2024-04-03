# tdd

# flake8 control
docker-compose run --rm app sh -c "flake8"

# to build django project
docker-compose run --rm app sh -c "django-admin startproject app ."

# to run the project with docker-compose
docker-compose up

# to run test the project with docker-compose
docker-compose run --rm app sh -c "python manage.py test"


