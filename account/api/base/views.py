from account.models import Profile, User
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from utils.base.email_service import email_service
from utils.base.errors import ApiResponse
from utils.base.general import get_tokens_for_user

from . import serializers
from .permissions import SuperPerm
from .tokens import password_reset_generator
from .utils import send_verification_email


class TokenVerifyAPIView(APIView):
    """
    An authentication plugin that checks if a jwt
    access token is still valid and returns the user info.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=serializers.JWTTokenValidateSerializer,
        responses={200: serializers.UserSerializer}
    )
    def post(self, request, format=None):
        jwt_auth = JWTAuthentication()
        raw_token = request.data.get('token')
        validated_token = jwt_auth.get_validated_token(raw_token)
        user = jwt_auth.get_user(validated_token)

        serialized_user = serializers.UserSerializer(user)
        user_details = serialized_user.data

        return Response(data=user_details)


class TokenRefreshAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TokenRefreshSerializer

    @swagger_auto_schema(
        request_body=TokenRefreshSerializer,
        responses={200: TokenRefreshSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        # Update last login
        access = serializer.validated_data.get('access')
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(access)
        user = jwt_auth.get_user(validated_token)
        user.last_login = timezone.now()
        user.save()

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.LoginSerializer

    @swagger_auto_schema(
        request_body=serializers.LoginSerializer,
        responses={
            200: serializers.LoginResponseSerializer200,
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        user = User.objects.get(email=email)

        if user.is_active:
            if user.verified_email:
                # Get the user details with the user serializer
                s2 = serializers.UserSerializer(user)

                user_details = s2.data
                response_data = {
                    'tokens': get_tokens_for_user(user),
                    'user': user_details
                }

                # Update last login
                user.last_login = timezone.now()
                user.save()

                return Response(data=response_data)

            # Resend email verification
            send_verification_email(user, request)

            response = {
                'detail': ApiResponse.EMAIL_NOT_VERIFIED.detail,
                'code': ApiResponse.EMAIL_NOT_VERIFIED.code,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'detail': ApiResponse.ACCOUNT_NOT_ACTIVE.detail,
            'code': ApiResponse.ACCOUNT_NOT_ACTIVE.code,
        }, status=status.HTTP_400_BAD_REQUEST)


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        user: User = serializer.save()
        user_serializer = serializers.UserSerializer(user)

        # Send email verification
        send_verification_email(user, request)

        user_details = user_serializer.data
        return Response(data=user_details, status='201')

    @swagger_auto_schema(
        request_body=serializers.RegisterSerializer,
        responses={201: serializers.UserSerializer}
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ResendEmailVerificationView(generics.GenericAPIView):
    """
    Resend email verification.

    Send email verification to the user's email address if the user is not verified.
    """

    permission_classes = (SuperPerm,)
    serializer_class = serializers.ResendEmailSerializer

    @swagger_auto_schema(
        responses={200: serializers.RegisterResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        user: User = serializer.validated_data.get('email')

        # Resend email verification
        send_verification_email(user, request)

        return Response(data={'message': 'Email sent successfully'})


class ValidateEmailVerificationTokenView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.EmailTokenValidateSerializer

    @swagger_auto_schema(
        responses={
            200: serializers.UserSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = serializer.validated_data.get('user')
        user.verified_email = True
        user.save()

        serialized = serializers.UserSerializer(user)
        return Response(serialized.data)


class ForgetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: serializers.ForgetPasswordResponseSerializer
        },
        request_body=serializers.ForgetPasswordSerializer,
    )
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        try:
            user: User = User.objects.get(email=email)

            # Get email tokens for user
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = password_reset_generator.make_token(user)

            # Send email to user
            email_service.send_html(
                email=user.email,
                subject='Password Reset',
                template='account/email/password_reset.html',
                context={
                    'user_name': user.profile.get_fullname,
                    'uidb64': uidb64,
                    'token': token,
                    'CLIENT_RESET_URL': settings.CLIENT_RESET_URL,
                },
                request=self.request,
                fail=True,
            )
        except User.DoesNotExist:
            pass

        return Response({
            'detail': 'Password reset email sent if the email exists',
        })


class ValidateResetPasswordTokenView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ResetPasswordTokenValidateSerializer

    @swagger_auto_schema(
        responses={
            200: serializers.UserSerializer,
        }
    )
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'message': 'Token is valid',
        })


class ForgetResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.object

    @swagger_auto_schema(
        request_body=serializers.ResetPasswordSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = serializers.ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Ensures reset link is not invalid
        user.last_login = timezone.now()
        user.save()

        return Response({
            'detail': 'Password reset successful.'
        })

    def get_queryset(self):
        return User.objects.filter(active=True)


class UserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        return User.objects.all().order_by('email')


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    lookup_field = 'id'
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ProfileSerializer
    http_method_names = ['get', 'patch']

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user.id)

    def get_queryset(self):
        return Profile.objects.all()
