# JS stuff
FROM node:17 as js_build

WORKDIR /build/web/js

COPY web/js .

RUN mkdir /build/static
RUN yarn install
RUN yarn run build

# Python stuff
FROM python:3.9

WORKDIR /app

COPY . .
COPY --from=js_build /build/static/* ./static/

RUN python -m pip install -r requirements.txt
RUN python -m pip install gunicorn

RUN useradd -u 8877 scpwiki
USER scpwiki

EXPOSE 8000
CMD ["gunicorn", "scpdev.wsgi", "-w", "8", "-b", "127.0.0.1:8000"]
