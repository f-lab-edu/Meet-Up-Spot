# Pull base image
FROM python:3.11.5

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /Meet-Up-Spot

# Install dependencies
RUN pip install pipenv
COPY ./Pipfile ./Pipfile.lock /Meet-Up-Spot/
RUN pipenv install --system --dev

COPY ./main.py /Meet-Up-Spot/main.py
COPY ./alembic /Meet-Up-Spot/alembic
COPY ./alembic.ini /Meet-Up-Spot/alembic.ini
COPY ./app /Meet-Up-Spot/app
COPY ./prestart.sh /Meet-Up-Spot/prestart.sh
COPY docker/entrypoint.sh  /Meet-Up-Spot/entrypoint.sh 
RUN chmod +x /Meet-Up-Spot/entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]


EXPOSE 8000
ENV PYTHONPATH=/Meet-Up-Spot