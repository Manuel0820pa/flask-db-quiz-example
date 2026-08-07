import os


class BaseConfig:
    """Configuración compartida entre entornos."""

    DEBUG = False
    TIME_ZONE = "UTC"

    @staticmethod
    def _database_uri_from_parts():
        dbuser = os.environ["DBUSER"]
        dbpass = os.environ["DBPASS"]
        dbhost = os.environ["DBHOST"]
        dbname = os.environ["DBNAME"]
        return f"postgresql+psycopg2://{dbuser}:{dbpass}@{dbhost}/{dbname}"


class DevelopmentConfig(BaseConfig):
    """Configuración para desarrollo local (incluye Docker/devcontainer)."""

    DEBUG = True

    def __init__(self):
        self.DATABASE_URI = self._database_uri_from_parts()


class ProductionConfig(BaseConfig):
    """
    Configuración para producción.

    Usa la variable de entorno estándar DATABASE_URL (formato usado por
    Railway, Render, Heroku, etc.) si está presente; si no, arma la URI
    a partir de variables individuales (DBUSER/DBPASS/DBHOST/DBNAME).
    """

    DEBUG = False

    def __init__(self):
        if "WEBSITE_HOSTNAME" in os.environ:
            self.ALLOWED_HOSTS = [os.environ["WEBSITE_HOSTNAME"]]
        else:
            self.ALLOWED_HOSTS = []

        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            # Railway/Render suelen dar "postgresql://", SQLAlchemy necesita el driver explícito
            self.DATABASE_URI = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        else:
            self.DATABASE_URI = self._database_uri_from_parts()


def get_config():
    is_prod_env = "WEBSITE_HOSTNAME" in os.environ or os.environ.get("FLASK_ENV") == "production"
    if is_prod_env:
        return ProductionConfig()  # pragma: no cover
    return DevelopmentConfig()