# Pull base image
FROM python:3.11.5

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_ENV "proudction"

WORKDIR /Meet-Up-Spot

# Install python dependencies
RUN pip install pipenv
COPY ./Pipfile ./Pipfile.lock /Meet-Up-Spot/
RUN pipenv install --system --dev

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm
# Install MJML
RUN npm install -g mjml

# Create directory for MJML build files
RUN mkdir -p /Meet-Up-Spot/app/email-templates/build/


COPY ./main.py /Meet-Up-Spot/main.py
COPY ./alembic /Meet-Up-Spot/alembic
COPY ./alembic.ini /Meet-Up-Spot/alembic.ini
COPY ./app /Meet-Up-Spot/app
COPY ./test_prestart.sh /Meet-Up-Spot/test_prestart.sh
COPY docker/entrypoint.sh  /Meet-Up-Spot/entrypoint.sh 
RUN chmod +x /Meet-Up-Spot/entrypoint.sh


RUN for file in /Meet-Up-Spot/app/email-templates/src/*.mjml; do \
    name=$(basename $file .mjml); \
    mjml $file -o /Meet-Up-Spot/app/email-templates/build/${name}.html; \
    done


ENTRYPOINT ["./entrypoint.sh"]


EXPOSE 8000
ENV PYTHONPATH=/Meet-Up-Spot