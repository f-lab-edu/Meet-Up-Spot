ENV_FILE ?= docker/test.env
DOCKER_COMPOSE_TEST = docker-compose -f docker/testing.yml
DOCKER_COMPOSE_DEV = docker-compose -f docker/development.yml
PIPENV_RUN = PIPENV_DOTENV_LOCATION=$(ENV_FILE) pipenv run


.PHONY: build test_in_actions test_mark test_one run_pgadmin first_user meet-build meet-up meet-down meet-initial_data set-pythonpath

prestart:
	echo 'export PYTHONPATH="$$(pwd)"' > set_pythonpath.sh
	bash set_pythonpath.sh
	rm set_pythonpath.sh

build:
	$(DOCKER_COMPOSE_TEST) build

prepare_db: prestart
	$(DOCKER_COMPOSE_TEST) up test-db -d
	$(PIPENV_RUN) alembic upgrade head
	$(PIPENV_RUN) python app/initial_data.py

prepare_redis:
	$(DOCKER_COMPOSE_TEST) up test-redis -d

test_common:
	-$(PIPENV_RUN) pytest -s -v -m "not isolated" --cov --cov-report=term
	-$(PIPENV_RUN) pytest -s -v -n auto -m "isolated" --cov --cov-append --cov-report=term
	$(DOCKER_COMPOSE_TEST) down

test_in_actions: prepare_db
	$(PIPENV_RUN) pytest -s -v -m "not isolated" --cov --cov-report=term
	$(PIPENV_RUN) pytest -s -v -n auto -m "isolated" --cov --cov-append --cov-report=xml:./coverage.xml
	$(DOCKER_COMPOSE_TEST) down

test_mark: prepare_db test_common

test_one: prepare_db prepare_redis
	$(DOCKER_COMPOSE_TEST) up  -d test-db test-redis
	-$(PIPENV_RUN) pytest -s -v ${test-path}
	$(DOCKER_COMPOSE_TEST) down

profile:prepare_db
	$(PIPENV_RUN) python profiling.py
	$(DOCKER_COMPOSE_TEST) down

run_pgadmin:
	$(DOCKER_COMPOSE_TEST) up -d pgadmin

first_user:
	docker-compose run --rm web python app/initial_data.py

meet-build:
	$(DOCKER_COMPOSE_DEV) build 

meet-up:
	$(DOCKER_COMPOSE_DEV) up 

meet-down:
	docker-compose down

meet-initial-data:
	$(DOCKER_COMPOSE_DEV) exec web python app/initial_data.py
