# RuFoundation

**RuFoundation** is a Wiki engine compatible with Wikidot developed by Russian SCP Branch.

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
