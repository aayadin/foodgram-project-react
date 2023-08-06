from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import serializers
from .models import Cart, Favorite, Ingredient, Recipe, Tag
from .pagination import CustomPagination


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagsSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientsSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        'ingredientamount_set__ingredient'
    )
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.GetRecipesSerializer
        return serializers.CreateUpdateDeleteRecipesSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.user != instance.author:
            return Response(
                {'detail': 'У вас нет прав для удаления этого рецепта.'},
                status=status.HTTP_403_FORBIDDEN
            )

        self.perform_destroy(instance)
        return Response(
            {'detail': 'Рецепт успешно удален.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated], url_name='favorite',
            url_path='favorite')
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        favorite_recipe_ids = list(
            Favorite.objects.filter(user=request.user).values_list(
                'model_to_subscribe', flat=True
            )
        )

        if request.method == 'POST':
            if recipe.id in favorite_recipe_ids:
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(
                user=request.user,
                model_to_subscribe=recipe
            )
            serializer = serializers.LimitRecipesSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            if recipe.id not in favorite_recipe_ids:
                return Response(
                    {'errors': 'Рецепт не найден в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite = Favorite.objects.get(
                user=request.user,
                model_to_subscribe=recipe
            )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated],
            url_name='shopping_cart', url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            cart_item, created = Cart.objects.get_or_create(
                user=user,
                model_to_subscribe=recipe
            )
            if created:
                serializer = serializers.LimitRecipesSerializer(
                    cart_item.recipe
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'errors': 'Рецепт уже в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif request.method == 'DELETE':
            try:
                cart_item = Cart.objects.get(
                    user=user, model_to_subscribe=recipe
                )
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Cart.DoesNotExist:
                return Response(
                    {'errors': 'Рецепт не найден в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_name='download_shopping_cart',
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        cart_items = Cart.objects.filter(user=user)

        response = HttpResponse(content_type='text/plain')
        type_name = 'attachment; filename="shopping_cart.txt"'
        response['Content-Disposition'] = type_name

        for cart_item in cart_items:
            for ingr_amount in cart_item.recipe.ingredientamount_set.all():
                ingredient_name = ingr_amount.ingredient.name
                amount = ingr_amount.amount
                response.write(f"{ingredient_name} - {amount}\n")
        return response
