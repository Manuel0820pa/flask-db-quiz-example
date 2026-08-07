import click
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class BaseModel(DeclarativeBase, MappedAsDataclass):
    pass


db = SQLAlchemy(model_class=BaseModel)
migrate = Migrate()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, static_folder="static")

    # Load configuration for prod vs. dev (ver flaskapp/config.py)
    from .config import get_config

    app.config.from_object(get_config())

    # Configure the database
    app.config.update(SQLALCHEMY_DATABASE_URI=app.config.get("DATABASE_URI"), SQLALCHEMY_TRACK_MODIFICATIONS=False)

    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    from . import quizzes

    app.register_blueprint(quizzes.bp)

    @app.route("/api/health")
    def health():
        return {"status": "ok"}, 200

    @app.cli.command("seed")
    def seed_data():
        if quizzes.Quiz.seed_data_if_empty():
            click.echo("Quiz seeded!")
        else:
            click.echo("Already seeded!")

    return app