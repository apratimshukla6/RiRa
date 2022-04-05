FROM python:3.10

# install client libs
RUN apt update -y && apt upgrade -y
RUN apt install -y ffmpeg opus-tools

# set environment variables
RUN mkdir -p /usr/src/app

# copy over setup files
COPY Pipfile /usr/src/app

# set working directory
WORKDIR /usr/src/app

# install dependencies
RUN python -m pip install --upgrade pip
RUN python -m pip install pipenv
RUN python -m pipenv install --deploy --ignore-pipfile

# copy remaining files
COPY . /usr/src/app

# start bot
CMD ["pipenv", "run", "python", "-m", "rira"]
