from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


class EmailService:

    @classmethod
    def build_context(cls, context):
        """
        Build context function

        :param context: context of email
        :type context: dict
        :return: context of email
        :rtype: dict
        """
        default_context = {
            "APP_NAME": settings.APP_NAME,
            'CLIENT_DOMAIN': settings.CLIENT_DOMAIN,
        }
        return {
            **default_context,
            **context
        }

    @classmethod
    def send_html(cls, email, subject, template, context, request=None, fail=True):
        """
        Send html mail function

        :param email: email address
        :type email: str
        :param subject: subject of email
        :type subject: str
        :param template: email template path
        :type template: str
        :param context: context of email
        :type context: dict
        :param request: current http request, defaults to None
        :type request: Request, optional
        :param fail: option to fail silently if there is an error, defaults to True
        :type fail: bool, optional
        :return: True if mail is sent, False otherwise
        :rtype: bool
        """
        message = render_to_string(
            template, cls.build_context({
                **context,
                "subject": subject,
            }), request)
        return cls.send_message(email, subject, message, fail)

    @classmethod
    def send_message(cls, email, subject, message, fail=True):
        """
        Send message function

        :param email: email address
        :type email: str
        :param subject: subject of email
        :type subject: str
        :param message: message of email
        :type message: str
        :param fail: option to fail silently if there is an error, defaults to True
        :type fail: bool, optional
        :return: True if mail is sent, False otherwise
        :rtype: bool
        """
        if settings.DEBUG is True:
            print(message)

        if settings.OFF_EMAIL:
            return True

        val = send_mail(
            subject=subject, message=message,
            html_message=message, from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email], fail_silently=fail)

        return True if val else False


email_service = EmailService()
