# SCP-dev

Experimental pet project Wiki engine compatible with Wikidot

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

By default, there are no pages in the website.

This also includes `nav:top` and `nav:side` which are critical for proper appearance.

You can create some by running the following command:

- `python manage.py seed`
