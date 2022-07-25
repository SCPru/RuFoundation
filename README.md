<div align="center">
  <h1>RuFoundation</h1>
  <h3>Wiki engine compatible with Wikidot developed by Russian SCP Branch</h3>
  <h4><a href="https://boosty.to/scpfanpage">#StandWithSCPRU</a></h4>
  <img src="https://i.kym-cdn.com/photos/images/facebook/001/839/765/e80.png" width="300px" alt="scp-ru">
</div>


## Requirements

Note: this is what I tested with, your mileage may differ.

- Windows 10
- NodeJS v17.3.0
- Python 3.10.1

## How to launch

- First navigate to `web/js` and execute `yarn install`
- After that, from the root project directory, run:
  - `pip install -r requirements.txt`
  - `python manage.py migrate`
  - `python manage.py runserver --watch`

## Seeding the database

To start working, the following objects are required:

- Minimally one website record (for localhost)
- Some pages (such as `nav:top` or `nav:side`) that are critical for proper appearance 

You can provision these basic structures by running the following commands:

- `python manage.py createsite -s scp-ru -d localhost -t "SCP Foundation" -H "Russian branch"`
- `python manage.py seed -s scp-ru`

## Running in Docker

### Requirements (tested with):

- Docker 20.10.14
- Docker-Compose 1.29.2

### Getting started

To start the project, use:

- `docker-compose up`

To completely delete all data, use:

- `docker-compose down`
- `rm -rf ./files ./archive ./postgresql`

To create users, sites and seed inside the database, start the project and afterwards use syntax such as this:

- `docker exec -it scpdev_web python manage.py createsite -s scp-ru -d localhost -t "SCP Foundation" -H "Russian branch"`
- `docker exec -it scpdev_web seed -s scp-ru`

To update current app that is running, do:

- `docker-compose up -d --no-deps --build web`

Note: in more recent versions, you may want to use `docker compose` instead of `docker-compose`.

