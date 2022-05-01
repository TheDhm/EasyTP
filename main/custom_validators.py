from django.core.validators import EmailValidator
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
from pandas import read_csv, read_excel
from django.utils.translation import gettext_lazy as _


@deconstructible
class EsiEmailValidator(EmailValidator):

    def validate_domain_part(self, domain_part):
        return False

    def __eq__(self, other):
        return isinstance(other, EsiEmailValidator) and super().__eq__(other)


def validate_emails_in_file(file):
    email_validator = EsiEmailValidator(allowlist=['esi.dz'],
                                        message='Enter a valid "@esi.dz" email address.')

    invalid_emails = []
    if str(file).endswith('.csv'):
        users = read_csv(file)
    else:
        users = read_excel(file)

    file.seek(0)

    for email in users.iloc[:, 0]:
        try:
            email_validator(email)
        except ValidationError:
            invalid_emails.append(email)

    if invalid_emails:
        raise ValidationError([
            ValidationError(_('Invalid email: %(email)s'),
                            params={'email': email})
            for email in invalid_emails
        ])


