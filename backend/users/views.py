from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet

from api.pagination import CustomPagination
from api.serializers import FollowSerializer
from .models import Follow, User
from .permissions import RegistrationOrReadOnly
from .serializers import (BaseUserSerializer, CreateUserSerializer,
                          GetUserSerializer)


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = [RegistrationOrReadOnly]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            if self.action == 'set_password':
                return SetPasswordSerializer
            return CreateUserSerializer
        return GetUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response = BaseUserSerializer(user)
        return Response(response.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            follow, created = Follow.objects.get_or_create(
                user=user, author=author
            )

            if created:
                return Response(
                    {'message': f'Вы подписались на {author.username}.'},
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'message': f'Вы уже подписаны на {author.username}.'},
                status=status.HTTP_200_OK
            )

        follow = get_object_or_404(Follow, user=user, author=author)
        follow.delete()
        return Response(
            {'message': f'Вы отписались от {author.username}.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subscriptions = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(subscriptions)
        response = FollowSerializer(pages, many=True,
                                    context={'request': request})
        return self.get_paginated_response(response.data)
