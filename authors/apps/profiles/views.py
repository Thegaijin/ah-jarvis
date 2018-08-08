from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from .models import Profile
from .renderers import ProfileJSONRenderer
from .serializers import ProfileSerializer
from .exceptions import ProfileDoesNotExist


class ProfileRetrieveAPIView(RetrieveAPIView):
    permission_classes = (AllowAny,)
    renderer_classes = (ProfileJSONRenderer,)
    serializer_class = ProfileSerializer

    def retrieve(self, request, username, *args, **kwargs):
        try:
            profile = Profile.objects.select_related('user').get(
                user__username=username
            )

        except Profile.DoesNotExist:
            raise ProfileDoesNotExist

        serializer = self.serializer_class(profile)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileFollowAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (ProfileJSONRenderer,)
    serializer_class = ProfileSerializer

    def delete(self, request, username):
        ''' The current user is able to unfollow another user's profile. '''
        follower = request.user.profile

        # Get the profile of user being followed
        try:
            followed = Profile.objects.get(user__username=username)
        except Profile.DoesNotExist:
            raise NotFound('The user with this profile does not exist')

        follower.unfollow(followed)

        serializer = self.serializer_class(follower, context={
            'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, username):
        ''' The current user is able to follow another user's profile. '''
        follower = request.user.profile

        # Get the profile of user being followed
        try:
            followed = Profile.objects.get(user__username=username)
        except Profile.DoesNotExist:
            raise NotFound('The user with this profile does not exist')

        # A user cannot follow themselves
        if follower.pk is followed.pk:
            raise serializers.ValidationError('You cannot follow yourself')

        follower.follow(followed)

        serializer = self.serializer_class(follower, context={
            'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
