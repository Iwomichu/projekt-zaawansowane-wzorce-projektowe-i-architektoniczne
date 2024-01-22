# Yber Cargo 
Logistics software, loosely inspired by Uber Freight https://www.uberfreight.com/.

Project developed as course work for "Advanced design and architectural patterns" course on Jagiellonian University.

Heavy lifting in this project is done by [FastAPI](https://github.com/tiangolo/fastapi), [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy), [Pydantic](https://github.com/pydantic/pydantic), and [Jinja](https://github.com/pallets/jinja).

## Description
Project aims to help warehousing company to manage their objects and products. It does so by serving as a platform on which warehouse employees, transport providers, business clients, producers and retail customers can operate. 

### Features

* Warehouse employees can request supply of a good from the producer
* Business client can request a transport of good from the warehouse
* Transport provider can take transport requests
* Retail custom can buy individual items

## Requirements
* Docker (if Docker-based deployment)
* Python 3.10 with Poetry (development and deployment if locally deployed)

## Deployment
### Docker
1. Run `docker compose up`
2. After some time the entire application, consisting of a main server, a database server and a session server, will be online and available. To access it enter `http://localhost:8000` in your browser (if the default `.env` file was used)

### Local (and Development)
#### You need your own database for this. See Environmental Variables section for related configuration variables.
1. Run `poetry install` to install required packages in the Poetry-managed environment
2. Set all variables from `.env` file manually one by one (for instance `export ZWPA_ADMIN_LOGIN="admin"`)
3. After that, you can run `uvicorn zwpa.main:app --host 0.0.0.0 --port 8000` to start the main server on port `8000`. 
4. Next run `uvicorn cart_manager.main:app --host 0.0.0.0 --port 8050` to start the user session server on port `8050`. 

### Environmental variables

* `ZWPA_DATABASE_DATABASE` - name of database in which all required tables will be created
* `ZWPA_DATABASE_LOGIN` - login to the database to be used by the main server
* `ZWPA_DATABASE_PASSWORD`- password to the database to be used by the main server
* `ZWPA_ADMIN_LOGIN` - login for the head admin account of the main server
* `ZWPA_ADMIN_PASSWORD` - password for the head admin account of the main server
* `ZWPA_WEBSERVER_PORT` - port on which main server should be started
* `ZWPA_CART_MANAGER_PORT` - port on which user session manager should be started
* `ZWPA_CART_MANAGER_ACCESS_KEY` - access key to session manager that should be used (currently has no effect)