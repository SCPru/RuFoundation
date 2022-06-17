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

COPY requirements.txt .
RUN python -m pip install -r requirements.txt
RUN python -m pip install gunicorn

COPY --from=js_build /build/static/* ./static/

COPY . .

RUN useradd -u 8877 scpwiki
USER scpwiki

EXPOSE 8000
CMD ["gunicorn", "scpdev.wsgi", "-w", "8", "-b", "0.0.0.0:8000"]
