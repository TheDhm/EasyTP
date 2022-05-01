from django.core.validators import EmailValidator
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
from pandas import read_csv, read_excel


@deconstructible
class EsiEmailValidator(EmailValidator):

    def validate_domain_part(self, domain_part):
        return False

    def __eq__(self, other):
        return isinstance(other, EsiEmailValidator) and super().__eq__(other)


def validate_emails_in_file(file):
    email_validator = EsiEmailValidator()
    print("hello ", file)
    if str(file).endswith('.csv'):
        users = read_csv(file)
    else:
        users = read_excel(file)

    for email in users.iloc[:, 0]:
        print(email)
        email_validator(email)




