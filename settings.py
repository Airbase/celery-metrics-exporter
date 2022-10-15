import os

POSTGRES_URI = os.environ.get("DATABASE_URL")
# https://stackoverflow.com/questions/62688256/sqlalchemy-exc-nosuchmoduleerror-cant-load-plugin-sqlalchemy-dialectspostgre
# sqlalchemy deprecated the name: postgres and only postgresql now
# heroku doesn't allow update of DATABASE_URL config var
driver = POSTGRES_URI.split("://")[0]
if driver == "postgres":
    POSTGRES_URI = POSTGRES_URI.replace("postgres", "postgresql")
REDIS_BROKER = os.environ.get("REDIS_BROKER")
