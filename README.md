# Installation and launch

**Installation**

You can clone this application:

```bash 
git clone https://github.com/Blastz13/queue_fastapi.git
```

Next, you need to install the necessary libraries:

```bash
poetry install
poetry update
```
You need to set variables in the environment: 

`JWT_SECRET` — Secret JWT key

`JWT_ALGORITHM` — Encryption algorithm method

`POSTGRES_USER` — Database username

`POSTGRES_PASSWORD` — Database password

`POSTGRES_SERVER` — Database host

`POSTGRES_PORT` — Database port

`POSTGRES_DB` — Database name

`PGADMIN_DEFAULT_EMAIL` — Postgres admin email

`PGADMIN_DEFAULT_PASSWORD` — Postgres admin password

`MONGO_INITDB_ROOT_USERNAME` — Mongo database username

`MONGO_INITDB_ROOT_PASSWORD` — Mongo database password

**Launch**

Change directory from web app, create and apply migrations:

```bash
cd queue_fastapi
alembic revision --autogenerate -m 'Initial'
alembic upgrade head
```

Now you can start the server:

```bash
uvicorn main:app --reload
```

### License

Copyright © 2021 [Blastz13](https://github.com/Blastz13/).