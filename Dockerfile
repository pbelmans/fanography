FROM python:3.12-alpine

# configuration
ENV REPOSITORY=https://github.com/pbelmans/fanography.git
ENV APP_HOME=fanography
ENV PORT=80

# install
RUN pip install gunicorn
RUN apk update \
  && apk add git  \
  && git clone $REPOSITORY website \
  && apk del git
WORKDIR /website
RUN pip install .

# setup
WORKDIR /website/$APP_HOME
EXPOSE 80

# run
CMD exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 0 --access-logfile=- application:app
