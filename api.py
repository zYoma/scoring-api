#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Callable, Optional, Union

import abc
import datetime
import hashlib
import inspect
import json
import logging
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from optparse import OptionParser

from scoring import get_interests, get_score


SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}
REQUIRED_PAIR = [{'last_name', 'first_name'}, {'birthday', 'gender'}, {'email', 'phone'}]
ADMIN_SCORE = 42
DELTA_YEAR = 70


class ValidationBaseError(Exception, abc.ABC):
    def __init__(self):
        self.message = self.get_message()
        super().__init__(self.message)

    def get_message(self):
        raise NotImplementedError


class ValidationError(ValidationBaseError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__()

    def get_message(self):
        result = {}
        for err in self.errors:
            error_text = err.error_text
            if error_text not in result:
                result[error_text] = [err.field]
            else:
                result[error_text].append(err.field)

        return ', '.join(f'{err} {fields_list}' for err, fields_list in result.items())


class ConstrainError(ValidationBaseError):
    def get_message(self):
        return f'Должна присутствовать хотя бы одна пара полей: {REQUIRED_PAIR}'


class BaseError(abc.ABC):
    error_text: str = ''

    def __init__(self, field):
        self.field = field


class MissingError(BaseError):
    error_text = 'Пропущены обязательные поля:'


class RequiredError(BaseError):
    error_text = 'Следующие поля не должны быть пустыми:'


class FieldTypeError(BaseError):
    error_text = 'Поля имеют не верный тип:'


class BaseModel(abc.ABC):
    root_validate: Optional[Callable] = None

    def __init__(self, **data: Any) -> None:
        error = False
        self.error = None

        self.__fields__ = self._get_class_fields()
        values, fields_set, validation_error = self._validate_model(data)
        if validation_error:
            self.error = validation_error
            error = True

        # если нет ошибок на предыдущем шаге, у конкретного класса есть главный валидатор и валидация не проходит
        if not error and self.root_validate and not self.root_validate(fields_set):
            self.error = ConstrainError()
            error = True

        if not error:
            # нет ошибок валидации, обновляем поля валидными значениями и сохраняем fields_set
            setattr(self, '__dict__', values)
            self.__fields__ = fields_set

    def _get_class_fields(self):
        """ Получает список всех публичных атрибутов экземпляра. """
        attributes = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        return [a for a in attributes if not (a[0].startswith('__') and a[0].endswith('__'))]

    def get_context(self):
        raise NotImplementedError

    def _validate_model(self, input_data: dict):
        """ Проверяет что есть все обязательные поля, есть значения в полях которые не могут быть пустыми.
            Если значение поля не прошло валидацию, добавляет информацию об этом в ошибки.
        """
        errors: list[Union[MissingError, RequiredError, FieldTypeError]] = []
        values = {}
        fields_set = set()
        for name, field in self.__fields__:
            value = input_data.get(name, None)
            if isinstance(field, BaseField):
                if value is None and field.required:
                    errors.append(MissingError(name))
                    continue

                if not value and not field.nullable:
                    errors.append(RequiredError(name))
                    continue

                if value and not field.is_valid(value):
                    errors.append(FieldTypeError(name))
                    continue

            if value is not None:
                fields_set.add(name)
            values[name] = value

        validation_error = ValidationError(errors) if errors else None
        return values, fields_set, validation_error


class BaseField(abc.ABC):
    def __init__(self, required: bool = False, nullable: bool = False):
        self.required = required
        self.nullable = nullable

    def is_valid(self, value) -> bool:
        raise NotImplementedError

    def __add__(self, other) -> str:
        return str(self) + str(other)

    @staticmethod
    def _validate_date(value, birthday=False) -> bool:
        now = datetime.datetime.now()
        try:
            date = datetime.datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return False

        if birthday:
            return True if now.year - date.year < DELTA_YEAR else False
        return True


class CharField(BaseField):
    def is_valid(self, value) -> bool:
        return isinstance(value, str)


class ArgumentsField(BaseField):
    def is_valid(self, value) -> bool:
        return isinstance(value, dict)


class EmailField(CharField):
    def is_valid(self, value) -> bool:
        return isinstance(value, str) and value.find('@') != -1


class PhoneField(BaseField):
    def is_valid(self, value) -> bool:
        # строка или число, длиной 11, начинается с 7
        if isinstance(value, str) or isinstance(value, int):
            value = str(value)
            return len(value) == 11 and value.startswith('7')

        return False


class DateField(BaseField):
    def is_valid(self, value) -> bool:
        return self._validate_date(value)


class BirthDayField(BaseField):
    def is_valid(self, value) -> bool:
        return self._validate_date(value, True)


class GenderField(BaseField):
    def is_valid(self, value) -> bool:
        return value in [UNKNOWN, MALE, FEMALE]


class ClientIDsField(BaseField, list):  # type: ignore
    def is_valid(self, value) -> bool:
        # Значение является не пустым списком, каждый элемент которого является целым числом
        if value and isinstance(value, list):
            return all([self.is_integer(i) for i in value])
        return False

    @staticmethod
    def is_integer(obj: Union[str, int]) -> bool:
        return isinstance(obj, int)


class ClientsInterestsRequest(BaseModel):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def get_context(self):
        return {"nclients": len(self.client_ids)}


def validate_on_line_score_fields(cls, fields_set: set[str]) -> bool:
    """Проверяет что есть хотя бы одна пара полей из REQUIRED_PAIR.
       Проверка реализовано через вхождение подмножества.
    """
    return True in [pair_set.issubset(fields_set) for pair_set in REQUIRED_PAIR]


class OnlineScoreRequest(BaseModel):
    root_validate = validate_on_line_score_fields

    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def get_context(self):
        return {"has": self.__fields__}


class MethodRequest(BaseModel):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    def get_context(self):
        return {}


def check_auth(request: MethodRequest) -> bool:
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode()).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode()).hexdigest()
    if digest == request.token:
        return True
    return False


def update_context(ctx: dict[str, Any], arguments: Union[OnlineScoreRequest, ClientsInterestsRequest]) -> None:
    context = arguments.get_context()
    ctx.update(context)


def get_arguments_and_error(data: MethodRequest):
    arguments_class = {
        'online_score': OnlineScoreRequest,
        'clients_interests': ClientsInterestsRequest
    }
    data_arguments = data.arguments if isinstance(data.arguments, dict) else {}
    arguments = arguments_class[data.method](**data_arguments)  # type: ignore
    error = arguments.error
    return arguments, error


def online_score(data: MethodRequest, ctx: dict[str, Any], store: Optional[str]):
    arguments, error = get_arguments_and_error(data)
    update_context(ctx, arguments)

    score = ADMIN_SCORE
    if data.login != ADMIN_LOGIN:
        score = get_score(store, **{k: v for k, v in arguments.__dict__.items() if k in arguments.__fields__})
    return {"score": score}, error


def clients_interests(data: MethodRequest, ctx: dict[str, Any], store: Optional[str]):
    arguments, error = get_arguments_and_error(data)
    update_context(ctx, arguments)
    interests = {client_id: get_interests(store, client_id) for client_id in arguments.client_ids}
    return interests, error


def get_error(error_code: int, message: str = None) -> tuple[str, int]:
    if message:
        return message, error_code
    return ERRORS[error_code], error_code


def method_handler(request: dict[str, Any], ctx: dict[str, Any], store: Optional[str]) -> tuple[str, int]:
    available_methods = {
        'online_score': online_score,
        'clients_interests': clients_interests
    }
    body = request.get('body')
    if not body:
        return get_error(INVALID_REQUEST)

    data = MethodRequest(**body)
    if error := data.error:
        return get_error(INVALID_REQUEST, error.get_message())
    if not check_auth(data):
        return get_error(FORBIDDEN)

    try:
        response, error = available_methods[data.method](data, ctx, store)  # type: ignore
    except KeyError:
        return get_error(BAD_REQUEST)

    return (response, OK) if not error else get_error(INVALID_REQUEST, error.get_message())


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    @staticmethod
    def get_request_id(headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except Exception:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except (ValidationError, ConstrainError) as e:
                    logging.exception("Validation error: %s" % e)
                    code = INVALID_REQUEST
                    response = e.message
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
