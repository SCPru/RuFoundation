# Rust stuff
FROM rust:1.63-buster AS rust_build

WORKDIR /build

COPY ftml/Cargo.lock .
COPY ftml/Cargo.toml .

RUN mkdir src
RUN touch src/lib.rs

RUN cargo build --release

COPY ftml .

RUN cargo build --release

# JS stuff
FROM node:24-slim AS js_build

RUN mkdir -p /build/static

WORKDIR /build/web/js
COPY web/js .
RUN yarn install
RUN yarn run build

# Python stuff
FROM python:3.13.2

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install -r requirements.txt
RUN python -m pip install gunicorn

COPY . .
COPY --from=js_build /build/static/* ./static/
COPY --from=rust_build /build/target/release/libftml.so ./ftml/ftml.so

RUN useradd -u 8877 scpwiki
RUN chown scpwiki:scpwiki /app -R

USER scpwiki

RUN python manage.py collectstatic

EXPOSE 8000
ENTRYPOINT [ "./entrypoint.sh" ]
