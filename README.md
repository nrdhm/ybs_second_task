# Установка и запуск (вне докера)
## Подготовка
Приложению требуется python 3.7+.

Также нужна запущенная база данных postgres, которую можно запустить так:

```bash
export COMPOSE_FILE=docker-compose.yaml:docker-compose.local.yaml

cp example.env .env

docker-compose up db
```

## Установка

- Установить `pipenv`
- Склонировать репозиторий, найти в нем поддиректорию с приложением и войти в нее

    cd gift_app

- Создать виртуальное окружение и установить зависимости

    pipenv install --dev

- Войти в виртуальное окружени

    pipenv shell

- Указать имя хоста с базой данных

    export GIFT_APP_DB_HOST=localhost

- Создать нужные для работы таблицы

    python -m manage init-db

## Запуск тестов

    pytest -vvx gift_app/tests

## Запуск приложения

    python -m aiohttp.web gift_app.main:init_func

# Развертывание на сервере
- Скопировать на сервер файлы docker-compose.yaml и .env
- Запустить сервисы

    sudo docker stack deploy -c docker-compose.yaml ybs --with-registry-auth
