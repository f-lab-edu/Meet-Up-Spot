# Pull base image
FROM python:3.11.5

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /Meet-Up-Spot

# Install dependencies
RUN pip install pipenv
COPY Pipfile Pipfile.lock /Meet-Up-Spot/
RUN pipenv install --system --dev

COPY ./main.py .
COPY ./alembic /Meet-Up-Spot/alembic
COPY ./alembic.ini .
COPY ./app ./app
COPY ./prestart.sh .

EXPOSE 8000
ENV PYTHONPATH=/Meet-Up-Spot