<div align="center">
  <h1>RuFoundation</h1>
  <h3>Wiki engine compatible with Wikidot developed by Russian SCP Branch</h3>
  <h4><a href="https://boosty.to/scpfanpage">#StandWithSCPRU</a></h4>
  <img src="https://i.kym-cdn.com/photos/images/facebook/001/839/765/e80.png" width="300px" alt="scp-ru">
</div>


## Requirements

Note: this is what I tested with, your mileage may differ.

- Windows 10
- PostrgeSQL 17.2
- NodeJS v17.3.0
- Python 3.13.2
- Rust 1.63

## PostgreSQL configuration
Defaults is:
- Username: `postgress` (`POSTGRES_USER`)
- Password: `zaq123` (`POSTGRES_PASSWORD`)
- DB name: `scpwiki` (`POSTGRES_DB`)
- DB host: `localhost` (`DB_PG_HOST`)
- DB port: `5432` (`DB_PG_PORT`)

You can change it with given environment variables.

## How to launch

- First navigate to `web/js` and execute `yarn install`
- After that, from the root project directory, run:
  - `pip install -r requirements.txt`
  - `python manage.py migrate`
  - `python manage.py runserver --watch`

## Creating admin account

- Run `python manage.py createsuperuser --username Admin --email "" --skip-checks`
- Follow instructions in terminal

## Seeding the database

To start working, the following objects are required:

- Minimally one website record (for localhost)
- Some pages (such as `nav:top` or `nav:side`) that are critical for proper appearance 

You can provision these basic structures by running the following commands:

- `python manage.py createsite -s scp-ru -d localhost:8000 -t "SCP Foundation" -H "Russian branch"`
- `python manage.py seed`

## Running in Docker

### Requirements (tested with):

- Docker 20.10.14
- Docker-Compose 1.29.2

### Getting started

Make preparation for files folder
- `useradd -u 8877 scpwiki`
- `mkdir -m 774 -p files && chown :scpwiki files`

To start the project, use:
- `docker-compose up`

To completely delete all data, use:

- `docker-compose down`
- `rm -rf ./files ./archive ./postgresql`

To create users, sites and seed inside the database, start the project and afterwards use syntax such as this:

- `docker exec -it scpdev-web python manage.py createsite -s scp-ru -d localhost -t "SCP Foundation" -H "Russian branch"`
- `docker exec -it scpdev-web python manage.py seed`

If you run production server make sure you setup you real domain Instead of `localhost`

To update current app that is running, do:

- `docker-compose up -d --no-deps --build web`

Note: in more recent versions, you may want to use `docker compose` instead of `docker-compose`.

