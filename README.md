<p align="center">
  <a href="" rel="noopener">
 <img src="https://www.python.org/static/img/python-logo@2x.png" alt="Project logo"></a>
</p>

<h3 align="center">Users REST API</h3>


<p align="center"> Django Rest Framework project with full User API features
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Deployment](#deployment)
- [Usage](#usage)
- [Built Using](#built_using)
- [TODO](../TODO.md)
- [Contributing](../CONTRIBUTING.md)
- [Authors](#authors)
- [Acknowledgments](#acknowledgement)

## 🧐 About <a name = "about"></a>

A DRF project for Ures signup and login. It covers all features of Users and Security System for ensuring good security.

## 🏁 Getting Started <a name = "getting_started"></a>

### Prerequisites

For installing the project, you will need to have
- Python installed. Python version supported is `3.10`. The Github actions use 3.10 for running live tests.
- Must have PostgreSQL installed. You can use WSL2 to do this on Windows 10 and 11.

### Installing

A step by step series of examples that tell you how to get a development environment running.

Clone the project

```bash
git clone https://github.com/BISHOPDAN/users_api.git
cd users_api
```

Setup env & install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd users_api
mkdir logs
```

Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd users_api
mkdir logs
```

There are examples specific to your development enviroment. `env.dev.example` is for development and You can copy the example files to `.env` and fill in the values.

```bash
cp env.dev.example .env
```

Run migrations

```bash
python manage.py migrate
```

Run the server

```bash
python manage.py runserver
```


> For the database keys in the env file, you should use your postgres user and password. You can create a new user and password for the project. You can also use the default postgres user and password.


## 🔧 Running the tests <a name = "tests"></a>

Run tests to make sure all is working before you start contributing

```bash
pytest --no-cov
```

## 🎈 Usage <a name="usage"></a>

To run the API on your local system.

```bash
python manage.py runserver
```

API server will run on `http://localhost:8000/`. Visit [Swagger](http://localhost:8000/dan/) to read the Swagger API documentation.


## Contributing

Use the following steps below to contribute to this project.

1. First checkout to the `master` branch
2. Create a new branch for your feature
3. Make your changes
4. Commit your changes
5. Push your changes to your branch
6. Create a pull request to the `master` branch
7. Wait for review and merge


## ⛏️ Built Using <a name = "built_using"></a>

- [Django](https://www.djangoproject.com/) - Web Framework
- [Django Rest Framework](https://www.django-rest-framework.org/) - Building Web APIs
- [PostgreSQL](https://www.postgresql.org/) - Database
- [Redis](https://redis.io/) - In-memory data store
- [Python](https://www.python.org/) - Programming Language


## :book: Documentation <a name = "documentation"></a>

Things to note about the project

The Users Functionalities and profile after a user register
and verify his or her email then the user will login automatically.

## ✍️ Author <a name = "author"></a>

- [@BISHOPDAN](https://github.com/BISHOPDAN) - Project Setup & Initial work

## 🎉 Acknowledgements <a name = "acknowledgement"></a>

- Hat tip to anyone whose code was used
- Inspiration
- References
