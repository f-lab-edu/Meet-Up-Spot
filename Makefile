
ENV_FILE ?= test.env


build:
	docker-compose -f ./testing.yml build


test_in_actions:
	docker-compose -f ./testing.yml up test-db -d
	PIPENV_DOTENV_LOCATION=test.env pipenv run alembic upgrade head
	PIPENV_DOTENV_LOCATION=test.env pipenv run python app/initial_data.py
	-PIPENV_DOTENV_LOCATION=test.env pipenv run pytest -s -v -m "not isolated" --cov --cov-report=term
	-PIPENV_DOTENV_LOCATION=test.env pipenv run pytest -s -v -n auto -m "isolated" --cov --cov-append --cov-report=xml:./coverage.xml
	docker-compose -f ./testing.yml down 

test_mark:
	docker-compose -f ./testing.yml up test-db -d
	PIPENV_DOTENV_LOCATION=test.env pipenv run alembic upgrade head
	PIPENV_DOTENV_LOCATION=test.env pipenv run python app/initial_data.py
	-PIPENV_DOTENV_LOCATION=test.env pipenv run pytest -s -v -m "not isolated" --cov --cov-report=term
	-PIPENV_DOTENV_LOCATION=test.env pipenv run pytest -s -v -n auto -m "isolated" --cov --cov-append --cov-report=term
	docker-compose -f ./testing.yml down 

test_one:
	docker-compose -f ./testing.yml up test-db -d
	-PIPENV_DOTENV_LOCATION=test.env pipenv run pytest -s -v ${test-path}
	docker-compose -f ./testing.yml down 

run_pgadmin:
	docker-compose -f ./testing.yml up -d pgamdin


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
