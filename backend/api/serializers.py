from collections import defaultdict

from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from users.models import Follow
from users.serializers import GetUserSerializer
from . import const
from .models import Cart, Ingredient, IngredientAmount, Recipe, Tag


class LimitTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id',)


class TagsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class CreateUpdateIngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.ReadOnlyField(source='ingredient.name')
    amount = serializers.IntegerField(max_value=const.MAX_LEN_VALID,
                                      min_value=const.MIN_LEN_VALID)
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'amount', 'measurement_unit')


class CreateUpdateDeleteRecipesSerializer(serializers.ModelSerializer):
    ingredients = CreateUpdateIngredientAmountSerializer(many=True)
    tags = LimitTagSerializer(read_only=True, many=True)
    image = Base64ImageField(required=False, allow_null=True)
    cooking_time = serializers.IntegerField(max_value=const.MAX_LEN_VALID,
                                            min_value=const.MIN_LEN_VALID)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name',
                  'text', 'cooking_time',)

    def create_ingredients(self, ingredients_data, recipe):
        IngredientAmount.objects.bulk_create(
            IngredientAmount(ingredient=Ingredient.objects.get(id=ingredient['id']),
                             amount=ingredient['amount'],
                             recipe=recipe)
            for ingredient in ingredients_data
        )

    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')
        tags_data = self.initial_data.get('tags')
        recipe = Recipe.objects.create(**validated_data, image=image)
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        instance.tags.clear()
        tags_data = self.initial_data.get('tags')
        instance.tags.set(tags_data)
        instance.save()
        ingredients_data = validated_data.get('ingredients', [])
        instance.ingredients.clear()
        IngredientAmount.objects.filter(recipe=instance).all().delete()
        self.create_ingredients(ingredients_data, instance)
        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['ingredients'] = self.initial_data.get('ingredients')
        ret['tags'] = self.initial_data.get('tags')
        return ret


class GetRecipesSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(
        many=True,
        source='ingredientamount_set'
    )
    tags = TagsSerializer(read_only=True, many=True)
    image = Base64ImageField(required=False, allow_null=True)
    author = GetUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return user.fav_user.filter(model_to_subscribe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return user.cart_user.filter(model_to_subscribe=obj).exists()


class LimitRecipesSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False)

    def validate(self, attrs):
        user = self.context['request'].user
        if user.fav_user.filter(model_to_subscribe=self.obj).exists():
            raise serializers.ValdationError('Рецепт уже в избранном.')


    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.followers.all().exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[:int(limit)]
        return LimitRecipesSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.all().count()


class CartSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('user', 'recipe', 'ingredients')

    def get_ingredients(self, obj):
        ingredient_count = defaultdict(int)
        cart_items = Cart.objects.filter(user=obj.user)
        for cart_item in cart_items:
            for ingr_amount in cart_item.recipe.ingredientamount_set.all():
                ingredient_name = ingr_amount.ingredient.name
                ingredient_count[ingredient_name] += ingr_amount.amount
        return ingredient_count
