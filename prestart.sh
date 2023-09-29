pipenv run alembic upgrade head

# Create initial data in DB
pipenv run python app/initial_data.py