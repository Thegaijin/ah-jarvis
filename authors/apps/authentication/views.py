from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .models import User
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.decorators import list_route
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from .models import User

from authors.apps.core.email import SendMail

from authors.apps.core.email import SendMail
from django.contrib.auth import get_user_model
from .utils import generate_token
from .renderers import UserJSONRenderer
from .serializers import (
    LoginSerializer, RegistrationSerializer, UserSerializer,
    EmailSerializer, ResetPasswordSerializer,
)


class RegistrationAPIView(APIView):
    # Allow any user (authenticated or not) to hit this endpoint.
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = RegistrationSerializer

    def post(self, request):
        user = request.data.get('user', {})

        # The create serializer, validate serializer, save serializer pattern
        # below is common and you will see it a lot throughout this course and
        # your own work later on. Get familiar with it.
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = get_user_model().objects.filter(
            email=serializer.data.get("email")).first()
        token = generate_token.make_token(user)
        SendMail(
            "email.html",
            {
                'user': user,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode("utf-8"),
                'token': token
            },
            subject="Verify your account",
            to=[user.email]
        ).send()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VerifyAccount(APIView):
    """ Verify account on vian sent link """

    def get(self, request, uidb64, token):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and generate_token.check_token(user, token):
            user.is_confirmed = True
            user.save()
            return HttpResponse("Account was verified successfully")
        else:
            return HttpResponse('Activation link is invalid!')


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginSerializer

    def post(self, request):
        user = request.data.get('user', {})

        # Notice here that we do not call `serializer.save()` like we did for
        # the registration endpoint. This is because we don't actually have
        # anything to save. Instead, the `validate` method on our serializer
        # handles everything we need.
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        # There is nothing to validate or save here. Instead, we just want the
        # serializer to handle turning our `User` object into something that
        # can be JSONified and sent to the client.
        serializer = self.serializer_class(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        serializer_data = request.data.get('user', {})

        # Here is that serialize, validate, save pattern we talked about
        # before.
        serializer = self.serializer_class(
            request.user, data=serializer_data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class ForgotPasswordAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = EmailSerializer

    def post(self, request):
        # Get the email and pass it to the serializer for validation
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Sends the user an email with the link to the reset password page
        context = {
            "verification_url": settings.VERIFCATION_URL + serializer.data.get('token', None)
        }

        SendMail("email.html", context, to=[serializer.data.get(
            'email', None)], subject='Authors Haven Reset Password').send()
        return Response(status=status.HTTP_200_OK)


class ResetPasswordAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer

    def put(self, request):
        """ Allows the user to change their password. """
        # Should take the token, user_email and new_password
        reset_data = request.data.get('reset_data', {})

        serializer = self.serializer_class(data=reset_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(data="Password Reset Successful",
                        status=status.HTTP_200_OK)
