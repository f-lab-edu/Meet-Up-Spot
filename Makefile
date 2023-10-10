ENV_FILE ?= test.env
DOCKER_COMPOSE_TEST = docker-compose -f ./testing.yml
PIPENV_RUN = PIPENV_DOTENV_LOCATION=$(ENV_FILE) pipenv run
PYTHONPATH_SETTING = export PYTHONPATH=./:$$PYTHONPATH;

.PHONY: build test_in_actions test_mark test_one run_pgadmin first_user meet-build meet-up meet-down meet-initial_data

build:
	$(DOCKER_COMPOSE_TEST) build

prepare_db:
	$(DOCKER_COMPOSE_TEST) up test-db -d
	$(PIPENV_RUN) alembic upgrade head
	$(PIPENV_RUN) python app/initial_data.py

test_common:
	-$(PIPENV_RUN) pytest -s -v -m "not isolated" --cov --cov-report=term
	-$(PIPENV_RUN) pytest -s -v -n auto -m "isolated" --cov --cov-append --cov-report=term
	$(DOCKER_COMPOSE_TEST) down

test_in_actions: prepare_db
	$(PIPENV_RUN) pytest -s -v -m "not isolated" --cov --cov-report=term
	$(PIPENV_RUN) pytest -s -v -n auto -m "isolated" --cov --cov-append --cov-report=xml:./coverage.xml
	$(DOCKER_COMPOSE_TEST) down

test_mark: prepare_db test_common

test_one: prepare_db
	$(DOCKER_COMPOSE_TEST) up test-db -d
	-$(PYTHONPATH_SETTING) $(PIPENV_RUN) pytest -s -v ${test-path}
	$(DOCKER_COMPOSE_TEST) down

run_pgadmin:
	$(DOCKER_COMPOSE_TEST) up -d pgadmin

first_user:
	docker-compose run --rm web python app/initial_data.py

meet-build:
	docker-compose build

meet-up:
	docker-compose up

meet-down:
	docker-compose down

meet-initial-data:
	docker-compose exec web python app/initial_data.py
