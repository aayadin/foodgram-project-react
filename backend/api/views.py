from django.http import HttpResponse
from django_filters import rest_framework as f
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsAuthorOrReadOnly
from . import serializers
from .filters import IngredientFilter, RecipeFilter
from .models import Cart, Favorite, Ingredient, Recipe, Tag
from .pagination import CustomPagination


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagsSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientsSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        'ingredientamount_set__ingredient'
    )
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = (f.DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.GetRecipesSerializer
        return serializers.CreateUpdateDeleteRecipesSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
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

        if not recipe.favorites.all().exists():
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
                    cart_item.model_to_subscribe
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'errors': 'Рецепт уже в корзине.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_items = Cart.objects.filter(
            user=user, model_to_subscribe=recipe
        )
        if cart_items.first():
            cart_items.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
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

        for i in cart_items:
            for ingr in i.model_to_subscribe.ingredientamount_set.all():
                ingredient_name = ingr.ingredient.name
                amount = ingr.amount
                response.write(f"{ingredient_name} - {amount}\n")
        return response
