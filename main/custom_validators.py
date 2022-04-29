from django.core.validators import EmailValidator
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError


@deconstructible
class EsiEmailValidator(EmailValidator):

    def validate_domain_part(self, domain_part):
        return False

    def __eq__(self, other):
        return isinstance(other, EsiEmailValidator) and super().__eq__(other)

