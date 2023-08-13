from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User
from . import const


class Tag(models.Model):
    """Модель тэга"""
    name = models.CharField(
        'Название',
        max_length=const.MAX_LEN_CHAR
    )
    color = models.CharField(
        'Цвет',
        max_length=const.MAX_LEN_COLOR,
        null=True
    )
    slug = models.SlugField(
        'slug',
        max_length=const.MAX_LEN_CHAR,
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента"""
    name = models.CharField(
        'Название',
        max_length=const.MAX_LEN_CHAR
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=const.MAX_LEN_CHAR
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта"""
    tags = models.ManyToManyField(
        Tag
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
    )
    name = models.CharField(
        'Название',
        max_length=const.MAX_LEN_CHAR,
    )
    image = models.ImageField(
        'Картинка',
        upload_to='api/images',
        null=True,
        default=None
    )
    text = models.TextField(
        'Описание',
        max_length=const.MAX_LEN_TEXT
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                const.MIN_LEN_VALID, message='Минимальное время 1 минута'),
            MaxValueValidator(
                const.MAX_LEN_VALID, message='Максимально время 32000 минут')
        ]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Избранные рецепты"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    model_to_subscribe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'model_to_subscribe'], name='unique_favorite'
            ),
        ]
        order_with_respect_to = 'model_to_subscribe'

    def __str__(self):
        return f'Рецепт {self.model_to_subscribe.name} в избранном'


class Cart(models.Model):
    """Корзина"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    model_to_subscribe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_cart'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Рецепты в корзине'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'model_to_subscribe'], name='unique_cart'
            )
        ]
        order_with_respect_to = 'model_to_subscribe'

    def __str__(self):
        return f'Рецепт {self.model_to_subscribe.name} в корзине'


class IngredientAmount(models.Model):
    """Кооличество ингредиентов"""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                const.MIN_LEN_VALID,
                message='Минимальное количество ингридиента 1'
            ),
            MaxValueValidator(
                const.MAX_LEN_VALID,
                message='Максимально время 32000 минут'
            )
        ]
    )

    class Meta:
        verbose_name = 'Количество ингридиента'
        verbose_name_plural = 'Количество ингридиентов'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'], name='unique_ingredients'
            )
        ]
        ordering = ['id']

    def __str__(self):
        return f'Количество {self.ingredient.name} - {self.amount}'
