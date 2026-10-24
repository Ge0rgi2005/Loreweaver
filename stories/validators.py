from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinLengthValidator

validate_author_name = RegexValidator(
    regex=r"^[^\W_]+(?:[ '-][^\W_]+)*$",
    message="Author name can only contain letters, spaces, hyphens, and apostrophes."
)

min_author_name_length = MinLengthValidator(
    2,
    message="Author name must be at least 2 characters long."
)

def non_whitespace_validator(value):
    if not value.strip():
        raise ValidationError("This field cannot be empty or contain only whitespace.")