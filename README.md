[![Open in GitHub Codespaces](https://img.shields.io/static/v1?style=for-the-badge&label=GitHub+Codespaces&message=Open&color=brightgreen&logo=github)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=pamelafox%2Fflask-db-quiz-example&machine=standardLinux32gb&devcontainer_path=.devcontainer%2Fdevcontainer.json&location=WestUs2)
[![Open in Remote - Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Remote%20-%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com%2Fpamelafox%2Fflask-db-quiz-example)

This repository includes a small Python Flask web site, made for demonstration purposes only.

## Arquitectura

### Arquitectura previa (legada)

El repositorio base (`pamelafox/flask-db-quiz-example`) ya venía organizado con Blueprints,
pero con dos puntos débiles frente a un entorno productivo real:

- **Modelos y rutas mezclados**: `flaskapp/quizzes.py` contenía en un solo archivo tanto las
  clases del ORM (`Quiz`, `Question`, `QuizScore`) como las rutas HTTP del Blueprint.
- **Configuración fragmentada y acoplada a Azure**: la configuración vivía en
  `flaskapp/config/development.py` y `flaskapp/config/production.py`, y la versión de
  producción dependía directamente de `azure.identity` para autenticarse contra la base de
  datos, lo que hacía imposible desplegar en otro proveedor sin reescribir esa lógica.
- **Sin contenedorización**: no existía `Dockerfile` ni `.dockerignore`; el único camino de
  despliegue documentado era Azure App Service vía `azd`.
- **Sin endpoint de salud**: no había forma estándar de monitorear si el servicio estaba vivo.

### Arquitectura nueva

- **`flaskapp/models.py`**: contiene únicamente los modelos de datos (`Quiz`, `Question`,
  `QuizScore`), separados de la capa de rutas.
- **`flaskapp/quizzes.py`**: contiene únicamente el Blueprint y las rutas HTTP, que ahora
  importan los modelos desde `models.py`.
- **`flaskapp/config.py`**: configuración centralizada en un solo archivo con clases
  (`BaseConfig`, `DevelopmentConfig`, `ProductionConfig`) en vez de módulos sueltos por
  entorno. `ProductionConfig` ahora prioriza la variable estándar `DATABASE_URL` (usada por
  Railway, Render, Heroku, etc.), y solo cae a la autenticación específica de Azure si
  detecta ese entorno — el proyecto deja de estar acoplado a un solo proveedor cloud.
- **`Dockerfile` (multi-stage, `python:3.12-slim`) y `.dockerignore`**: la app corre en un
  contenedor aislado con usuario no-root, con una etapa de build separada para mantener la
  imagen final ligera.
- **`GET /api/health`**: endpoint de diagnóstico que responde `{"status": "ok"}` para
  monitoreo en producción.

## Opening the project

This project has [Dev Container support](https://code.visualstudio.com/docs/devcontainers/containers), so it will be be setup automatically if you open it in Github Codespaces or in local VS Code with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

If you're not using one of those options for opening the project, then you'll need to:

1. Create a [Python virtual environment](https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments) and activate it.

2. Install the requirements:

    ```shell
    python3 -m pip install -r requirements-dev.txt
    ```

3. Install the pre-commit hooks:

    ```shell
    pre-commit install
    ```

## Local development


1. Create an `.env` file using `.env.sample` as a guide. Set the value of `DBNAME` to the name of an existing database in your local PostgreSQL instance. Set the values of `DBHOST`, `DBUSER`, and `DBPASS` as appropriate for your local PostgreSQL instance. If you're in the Dev Container, copy the values exactly from `.env.sample`.

2. Apply migrations to database:

```console
python3 -m flask db upgrade --directory src/flaskapp/migrations
```

3. Load in seed data (to create first quiz):

```console
python3 -m flask seed
```

4. Run the server:

```console
flask --app src/app run
```

5. Click 'http://127.0.0.1:5000' in the terminal, which should open the website in a new tab.
6. Open the quiz linked from the index page.
7. Answer the quiz and submit, notice the high scores update below.

## Running with Docker

You can also build and run the app in a container instead of a local virtualenv:

```console
docker build -t flask-quiz .
docker run -p 8000:8000 -e DBHOST=host.docker.internal -e DBNAME=app -e DBUSER=app_user -e DBPASS=app_password flask-quiz
```

Then visit `http://localhost:8000/api/health` to confirm the container is up and connected to the database.

## Tests

1. Install the development requirements:

```console
python3 -m pip install -r requirements-dev.txt
playwright install --with-deps
```

2. Run the tests:

```console
python3 -m pytest
```

## Deployment

This repository is set up for deployment on Azure using the configuration files in the `infra` folder.

![Architecture diagram: App Service, PostgreSQL Flexible server, Log Analytics](readme_diagram.png)

1. Sign up for a [free Azure account](https://azure.microsoft.com/free/?WT.mc_id=python-79461-pamelafox)
2. Install the [Azure Dev CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd?WT.mc_id=python-79461-pamelafox). (If you open this repository in Codespaces or with the VS Code Dev Containers extension, that part will be done for you.)
3. Initialize a new `azd` environment:

    ```shell
    azd init
    ```

    It will prompt you to provide a name (like "flask-app") that will later be used in the name of the deployed resources.

4. Provision and deploy all the resources:

    ```shell
    azd up
    ```

    It will prompt you to login, pick a subscription, and provide a location (like "eastus"). Then it will provision the resources in your account and deploy the latest code. If you get an error with deployment, changing the location (like to "centralus") can help, as there may be availability constraints for some of the resources.

5. When azd has finished deploying, you'll see an endpoint URI in the command output. Visit that URI and you should see the quiz! 🎉

6. When you've made any changes to the app code, you can just run:

    ```shell
    azd deploy
    ```

### CI/CD pipeline

This project includes a Github workflow for deploying the resources to Azure
on every push to main. That workflow requires several Azure-related authentication secrets
to be stored as Github action secrets. To set that up, run:

```shell
azd pipeline config
```

### Security

#### Database

It is important to secure the databases in web applications to prevent unwanted data access.
This infrastructure uses the following mechanisms to secure the PostgreSQL database:

* Azure Firewall: The database is accessible only from other Azure IPs, not from public IPs. (Note that includes other customers using Azure).
* Admin Username: A unique string generated based on the resource name (*not* random, but not a standard name, either).
* Admin Password: Randomly generated and updated on each deploy.
* PostgreSQL Version: Latest available on Azure, version 14, which includes security improvements.

⚠️ To make your database connection more secure, consider:

1. Storing username/password in Key Vault. See [the django-quiz-app project](https://github.com/pamelafox/django-quiz-app) for example infrastructure files.
2. Using an Azure Virtual Network to connect the Web App to the Database. See [the django-on-azure project](https://github.com/tonybaloney/django-on-azure) for example infrastructure files.

#### Sessions

This Flask app does not currently use [sessions](https://flask.palletsprojects.com/en/2.3.x/quickstart/#sessions), so it doesn't require a secret key. However, if you do add a secret key in the future, you should store that securely in Key Vault. See [the django-quiz-app project](https://github.com/pamelafox/django-quiz-app) for infrastructure files that store secrets in Key Vault.

### Costs

Pricing varies per region and usage, so it isn't possible to predict exact costs for your usage.

You can try the [Azure pricing calculator](https://azure.com/e/6bf1c15e609249b3b223ca3ceadeba94) for the resources:

- Azure App Service: Free Tier with shared CPU cores, 1 GB RAM. [Pricing](https://azure.microsoft.com/pricing/details/app-service/linux/)
- PostgreSQL Flexible Server: Burstable Tier with 1 CPU core, 32GB storage. Pricing is hourly. [Pricing](https://azure.microsoft.com/pricing/details/postgresql/flexible-server/)
- Log analytics: Pay-as-you-go tier. Costs based on data ingested. [Pricing](https://azure.microsoft.com/pricing/details/monitor/)

⚠️ To avoid unnecessary costs, remember to take down your app if it's no longer in use,
either by deleting the resource group in the Portal or running `azd down`.
