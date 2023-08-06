import csv

from django.core.management.base import BaseCommand

from api.models import Ingredients


class Command(BaseCommand):
    help = 'Импорт ингредиентов из csv файла'

    def handle(self, *args, **options):
        with open(r'data/ingredients.csv',
                  encoding='utf8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                i = Ingredients(
                    name=row[0],
                    measurement_unit=row[1]
                )
                i.save()
            print('Импорт ингредиентов завершен')
