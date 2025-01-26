# Fanography

This is the repository to host [fanography.info](https://fanography.info).

## Flask instructions

Inside a new virtual environment, do

```shell
pip install Flask python-dotenv
pip install -e .
flask run
```

and you'll have a local copy running at <http://127.0.0.1:4000>.

## Docker instructions

This is currently not how the website is run, but in case you want to experiment,
here are the instructions:

```shell
docker build --tag "fanography" .
docker run -p 8888:80 -it fanography
```

If you want to use the local state of the repository, change `git clone` to

```Dockerfile
COPY . ./website
```
