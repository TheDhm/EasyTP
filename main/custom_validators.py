from django.core.validators import EmailValidator
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError


@deconstructible
class EsiEmailValidator(EmailValidator):

    def validate_domain_part(self, domain_part):
        return False

    def __eq__(self, other):
        return isinstance(other, EsiEmailValidator) and super().__eq__(other)


def validate_year(role, year):
    print(role, year)
    if role == 'S' and year == '':
        raise ValidationError(
            "The student's academic year must be specified."
        )
