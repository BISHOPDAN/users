from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from account.models import User
from utils.base.email_service import email_service

from .tokens import account_confirm_token


def send_verification_email(user: User, request=None):
    # Get email tokens for user
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_confirm_token.make_token(user)

    # Send email to user
    email_service.send_html(
        user.email,
        'Verify your email',
        'account/email/verify_email.html',
        {
            'user_name': user.profile.get_fullname,
            'uidb64': uidb64,
            'token': token
        },
        request,
        True,
    )
