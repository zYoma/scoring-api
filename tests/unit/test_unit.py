import pytest

from api import (
    ArgumentsField,
    BirthDayField,
    CharField,
    ClientIDsField,
    DateField,
    EmailField,
    GenderField,
    PhoneField
)


@pytest.mark.parametrize('value, result', [  # noqa
    (123, False),
    ('string', True),
    (['string'], False),
])
def test_char_field(value, result):
    field = CharField()
    is_valid = field.is_valid(value)
    assert is_valid == result


@pytest.mark.parametrize('value, result', [  # noqa
    (123, False),
    ('string', False),
    ({'key': 'value'}, True),
])
def test_arguments_field(value, result):
    field = ArgumentsField()
    is_valid = field.is_valid(value)
    assert is_valid == result


@pytest.mark.parametrize('value, result', [  # noqa
    ('mail@mail.ru', True),
    ('string', False),
    (123, False),
])
def test_email_field(value, result):
    field = EmailField()
    is_valid = field.is_valid(value)
    assert is_valid == result


@pytest.mark.parametrize('value, result', [  # noqa
    ('12345670000', False),
    ('76543210000', True),
    (76543210000, True),
    ('765432100001', False),
    (765432100001, False),
    (12345670000, False),
])
def test_phone_field(value, result):
    field = PhoneField()
    is_valid = field.is_valid(value)
    assert is_valid == result


@pytest.mark.parametrize('value, result', [  # noqa
    ('20.04.88', False),
    ('20.04.1970', True),
    ('20/04/1970', False),
    ('20-04-1970', False),
    ('2005-08-09T18:31:42', False),
])
def test_date_field(value, result):
    field = DateField()
    is_valid = field.is_valid(value)
    assert is_valid == result


@pytest.mark.parametrize('value, result', [  # noqa
    ('20.04.88', False),
    ('20.04.1970', True),
    ('20/04/1970', False),
    ('20-04-1970', False),
    ('2005-08-09T18:31:42', False),
    ('20.04.1953', True),
    ('20.04.1952', False),
])
def test_birthday_field(value, result):
    field = BirthDayField()
    is_valid = field.is_valid(value)
    assert is_valid == result


@pytest.mark.parametrize('value, result', [  # noqa
    ('1', False),
    (1, True),
    (3, False),
])
def test_gender_field(value, result):
    field = GenderField()
    is_valid = field.is_valid(value)
    assert is_valid == result


@pytest.mark.parametrize('value, result', [  # noqa
    ('1, 2, 3', False),
    (1, False),
    ([], False),
    (['1', '2'], False),
    ([1, 2], True),
    ([0], True),
])
def test_clients_ids_field(value, result):
    field = ClientIDsField()
    is_valid = field.is_valid(value)
    assert is_valid == result
