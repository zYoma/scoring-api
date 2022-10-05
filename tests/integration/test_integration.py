import pytest
import requests


METHOD_URL = 'http://localhost:8080/method'
ARGUMENTS_FOR_ONLINE_SCORE = {
    "phone": 79298405555,
    "email": "wrwe@rwer",
    "first_name": "Петя",
    "last_name": "Иванок",
    "birthday": "20.04.1970",
    "gender": 2
}
CONSTRAIN_ERROR = "Должна присутствовать хотя бы одна пара полей: " \
                  "[{'last_name', 'first_name'}, {'birthday', 'gender'}, {'email', 'phone'}]"


@pytest.mark.parametrize('json, code', [  # noqa
    ({
        "account": "", "login": "", "method": "",
        "token": "", "arguments": ARGUMENTS_FOR_ONLINE_SCORE
    }, 400),
    ({
        "account": "", "login": "", "method": "new",
        "token": "", "arguments": ARGUMENTS_FOR_ONLINE_SCORE
    }, 400),
    ({
        "account": "", "method": "online_score",
        "token": "", "arguments": ARGUMENTS_FOR_ONLINE_SCORE
    }, 422),
    ({
        "login": "", "method": "clients_interests",
        "arguments": ARGUMENTS_FOR_ONLINE_SCORE
    }, 422),
])
def test_method_request_errors(json, code, server, mock_token):
    r = requests.post(METHOD_URL, json=json)
    assert r.status_code == code


@pytest.mark.parametrize('json, code, response', [  # noqa
    ({
        "account": "acc", "login": "admin", "method": "clients_interests",
        "token": "", "arguments": {"client_ids": [1, 2, 3], "date": "20.04.1970"}
    }, 200, {'1': {'key': 'value'}, '2': {'key': 'value'}, '3': {'key': 'value'}}),
    ({
        "account": "acc", "login": "admin", "method": "clients_interests",
        "token": "", "arguments": {"client_ids": [1, 2, 3]}
    }, 200, {'1': {'key': 'value'}, '2': {'key': 'value'}, '3': {'key': 'value'}}),
    ({
        "account": "acc", "login": "admin", "method": "clients_interests",
        "token": "", "arguments": {"client_ids": [], "date": "20.04.1970"}
    }, 422, "Следующие поля не должны быть пустыми: ['client_ids']"),
    ({
        "account": "acc", "login": "admin", "method": "clients_interests",
        "token": "", "arguments": {"client_ids": ['1', '2'], "date": "20.04.1970"}
    }, 422, "Поля имеют не верный тип: ['client_ids']"),
    ({
        "account": "acc", "login": "admin", "method": "clients_interests",
        "token": "", "arguments": {"client_ids": [1, 2], "date": "20-04-1970"}
    }, 422, "Поля имеют не верный тип: ['date']"),
    ({
        "account": "acc", "login": "admin", "method": "clients_interests",
        "token": "", "arguments": {}
    }, 422, "Пропущены обязательные поля: ['client_ids']"),
])
def test_clients_interests(json, code, response, server, mock_token):
    r = requests.post(METHOD_URL, json=json)
    assert r.status_code == code
    if r.status_code != 200:
        assert r.json()['error'] == response
    else:
        assert r.json()['response'] == response


@pytest.mark.parametrize('json, code, response, description', [  # noqa
    ({
        "account": "acc", "login": "admin", "method": "online_score",
        "token": "", "arguments": {
            "phone": 79298405555,
            "email": "wrwe@rwer",
            "first_name": "Петя",
            "last_name": "Иванок",
            "birthday": "20.04.1970",
            "gender": 2
        }
    }, 200, {'score': 42}, 'true data, admin'),
    ({
        "account": "acc", "login": "admin_2", "method": "online_score",
        "token": "", "arguments": {
            "phone": 79298405555,
            "email": "wrwe@rwer",
            "first_name": "Петя",
            "last_name": "Иванок",
            "birthday": "20.04.1970",
            "gender": 2
        }
    }, 200, {'score': 5.0}, 'true data'),
    ({
        "account": "acc", "login": "admin", "method": "online_score",
        "token": "", "arguments": {
            "phone": '79298405555',
            "email": "wrwe@rwer",
            "first_name": "Петя",
            "last_name": "Иванок",
            "birthday": "20.04.1970",
            "gender": 2
        }
    }, 200, {'score': 42}, 'Phone is str'),
    ({
        "account": "acc", "login": "admin", "method": "online_score",
        "token": "", "arguments": {
            "phone": '89298405555',
            "email": "wrwe@rwer",
            "first_name": "Петя",
            "last_name": "Иванок",
            "birthday": "20.04.1970",
            "gender": 2
        }
    }, 422, "Поля имеют не верный тип: ['phone']", 'bad phone'),
    ({
        "account": "acc", "login": "admin", "method": "online_score",
        "token": "", "arguments": {
            "phone": '89298405555',
            "email": "wrwerwer",
            "first_name": "Петя",
            "last_name": "Иванок",
            "birthday": "20.04.1970",
            "gender": 2
        }
    }, 422, "Поля имеют не верный тип: ['email', 'phone']", 'bad phone and email'),
    ({
        "account": "acc", "login": "admin", "method": "online_score",
        "token": "", "arguments": {
            "phone": '79298405555',
            "gender": 2
        }
    }, 422, CONSTRAIN_ERROR, 'constrain error'),
    ({
        "account": "acc", "login": "admin", "method": "online_score",
        "token": "", "arguments": {
            "birthday": "20.04.1970",
            "gender": 2
        }
    }, 200, {'score': 42}, 'true constrain pair'),
    ({
        "account": "acc", "login": "admin", "method": "online_score",
        "token": "", "arguments": {
            "phone": '89298405555',
            "email": "wrwe@rwer",
            "first_name": "",
            "birthday": "20.04.1970",
            "gender": 20
        }
    }, 422, "Поля имеют не верный тип: ['gender', 'phone']", 'bad gender and phone'),
])
def test_online_score(json, code, response, description, server, mock_token):
    r = requests.post(METHOD_URL, json=json)
    assert r.status_code == code
    if r.status_code != 200:
        assert r.json()['error'] == response, description
    else:
        assert r.json()['response'] == response, description
