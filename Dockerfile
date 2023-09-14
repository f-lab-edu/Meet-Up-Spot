# Pull base image
FROM python:3.11

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app/

# Install dependencies
RUN pip install pipenv
COPY Pipfile Pipfile.lock /app/
RUN pipenv install --system --dev

COPY ./app /app/

EXPOSE 8000
ENV PYTHONPATH=/app