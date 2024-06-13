from account.models import Profile, User
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.validators import validate_email
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from utils.base.validators import validate_special_char
from .tokens import account_confirm_token, password_reset_generator


class JWTTokenValidateSerializer(serializers.Serializer):
    token = serializers.CharField()


class JWTTokenResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        help_text=f"Refresh token will be used to generate new \
access token every {settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']} minutes ")
    access = serializers.CharField(
        help_text='Used in headers to authenticate users')
    access_expires_in = serializers.IntegerField(
        help_text='Time in seconds until access token expires')
    refresh_expires_in = serializers.IntegerField(
        help_text='Time in seconds until refresh token expires')


class SendMailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    subject = serializers.CharField()
    message = serializers.CharField()


class SendMailResponseSerializer(serializers.Serializer):
    email = serializers.EmailField()
    sent = serializers.BooleanField()


class ResendEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text='Email of user to verify')

    def validate_email(self, value):
        """
        Validate email address
        """
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'User with this email does not exist')
        if user.verified_email:
            raise serializers.ValidationError(
                'User with this email is already verified')
        return user


class OtpSerializer(serializers.Serializer):
    otp = serializers.IntegerField()


class TokenGenerateSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class TokenGenerateSerializerEmail(serializers.Serializer):
    email = serializers.EmailField(
        help_text='Email of user to verify and return tokens for')


class BaseValidateSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    generator: PasswordResetTokenGenerator = None

    def validate(self, attrs):
        uidb64 = attrs.get('uidb64')
        token = attrs.get('token')

        try:
            uidb64 = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=uidb64)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({
                'token': 'Invalid token'
            })

        if not self.generator.check_token(user, token):
            raise serializers.ValidationError({
                'token': 'Invalid token'
            })

        attrs['user'] = user
        return attrs


class EmailTokenValidateSerializer(BaseValidateSerializer):
    generator = account_confirm_token

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user: User = attrs.get('user')

        if user.verified_email:
            raise serializers.ValidationError({
                'token': 'Email already verified'
            })
        return attrs


class ResetPasswordTokenValidateSerializer(BaseValidateSerializer):
    generator = password_reset_generator


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    first_name = serializers.CharField(
        required=True, help_text='User first name',
        validators=[validate_special_char], max_length=30)
    last_name = serializers.CharField(
        required=True, help_text='User last name',
        validators=[validate_special_char], max_length=30)

    class Meta:
        model = User
        fields = ('password', 'email', 'first_name', 'last_name')

    def create(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')
        user = User.objects.create_user(email=email, password=password)

        # Get the profile and update the first and last names
        profile = user.profile
        profile.first_name = validated_data.get('first_name')
        profile.last_name = validated_data.get('last_name')
        profile.save()

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        # Get required info for validation
        email = attrs['email']
        password = attrs['password']

        """
        Check that the email is available in the User table
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": 'Please provide a valid email and password'})

        if not user.check_password(password):
            raise serializers.ValidationError(
                {"email": 'Please provide a valid email and password'})

        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'email',
            'profile'
        ]

    def validate_phoneno(self, value):
        if value:
            # Check if this phone has been used by anyone
            qset = User.objects.filter(phone=value)

            if self.instance:
                qset = qset.exclude(pk=self.instance.pk)

            exists = qset.exists()
            if exists:
                raise serializers.ValidationError(
                    'This phone number has already been used')

        return value

class ResetPasswordSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        # Validate uidb64 and token
        uidb64 = attrs.get('uidb64')
        token = attrs.get('token')

        try:
            uidb64 = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=uidb64)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({
                'token': 'Invalid token'
            })

        if not password_reset_generator.check_token(user, token):
            raise serializers.ValidationError({
                'token': 'Invalid token'
            })

        # Validate if the provided passwords are similar
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"password": "The two passwords differ."})

        attrs['user'] = user
        return attrs

    def save(self, **kwargs) -> User:
        """
        Save the new password
        """
        user: User = self.validated_data['user']
        password = self.validated_data['new_password']
        user.set_password(password)
        user.save()
        return user


class ForgetChangePasswordSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'new_password',
            'confirm_password', 'profile',)
        extra_kwargs = {
            'email': {'read_only': True},
        }

    def validate(self, attrs):
        # Validate if the provided passwords are similar
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if not new_password:
            raise serializers.ValidationError(
                {"new_password": "New password field is required."})

        if not confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Confirm password field is required."})

        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."})

        return attrs

    def update(self, instance, validated_data):
        # Set password
        new_password = validated_data.get('new_password')
        instance.set_password(new_password)
        instance.save()

        return instance


class RegisterResponseSerializer(serializers.Serializer):
    user = UserSerializer()


class ForgetPasswordResponseSerializer(serializers.Serializer):
    fullname = serializers.CharField(
        help_text='Fullname of token\'s user generated')
    email = serializers.CharField(help_text='Email of token\'s user generated')


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text='Email of user to reset password')


class LoginResponseSerializer200(serializers.Serializer):
    user = UserSerializer()
    tokens = JWTTokenResponseSerializer()
