# JS stuff
FROM node:17 as js_build

WORKDIR /build/web/js

COPY web/js .

RUN mkdir /build/static
RUN yarn install
RUN yarn run build

# Python stuff
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install -r requirements.txt
RUN python -m pip install gunicorn

COPY . .
COPY --from=js_build /build/static/* ./static/

RUN useradd -u 8877 scpwiki
RUN chown scpwiki:scpwiki /app -R

USER scpwiki

RUN python manage.py collectstatic

EXPOSE 8000
CMD ["gunicorn", "scpdev.wsgi", "-w", "8", "-b", "0.0.0.0:8000"]
