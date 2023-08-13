### Дипломный проект: Продуктовый помощник

[![Django-app workflow](https://github.com/aayadin/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg?branch=master)](https://github.com/aayadin/foodgram-project-react/actions/workflows/foodgram_workflow.yml)

## Описание
Продуктовый помощник - сайт для публикации и поиска рецептов. Рецепты можно добавлять в избранное и в корзину. Доступна функция скачивания списка покупок для рецептов, находящихся в корзине. Можно подписываться на второв рецептов.
## Сайт доступен по url:
```
http://yourfood.ddns.net
ip: 51.250.98.3
```
## Запуск проекта:
- Клонируйте репозиторий:
```
git clone https://github.com/aayadin/foodgram-project-react.git
```
- Из папки с файлом docker-compose выполните команду:
```
docker-compose up
```
- Выполните миграции:
```
docker-compose exec -T backend python manage.py migrate
```
- Создайте суперпользователя:
```
docker compose -f docker-compose.yml exec backend python manage.py createsuperuser
```
- Подключите статику:
```
docker-compose exec -T backend python manage.py collectstatic --no-input
```
## Импорт базы ингредиентов:
После применения миграций выполнить команду:
```
python manage.py import_ingredients
```
## Шаблон наполнения env-файла:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY='secret_key_agbnavkdjn4248962n'
DEBUG=False
ALLOWED_HOSTS='localhost'

```
## Для остановки сервисов выполнить:
```
docker-compose down
```
## Технологии
-Python v3.7
-Django
-DRF
-PostgresQL
-Nginx
-Gunicorn

## Автор
Андрей Ядин, практикующий геофизик, начинающий разработчик.