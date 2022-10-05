# scoring-api

#### Приложение написано в качестве учебного проекта.
Декларативный язык описания и система валидации запросов к HTTP API сервиса скоринга.

### Стек
Для запуска не требуется устанавливать никакие сторонние библиотеки.
- python 3.10


### Запуск
``` python scoring.py ```

### Конфигурация
Приложению можно передать путь к файлу с логами. Если путь передан, лог будет писаться в файл. Если не передан - в терминал.

``` python scoring.py -l log.log ```


### Разработка
Для работы линтеров потребуется установить зависимости в ваше окружение.
``` 
pip install poetry 
poetry install
```

Запуск тестов, линтеров
``` 
mypy .
flake8
pytest
``` 

### Использование
После запуска, сервис ожидает POST запрос по адресу:
``` 
localhost:8080/method
``` 

Пример запроса:
``` 
curl --request POST \
  --url http://localhost:8080/method \
  --header 'Content-Type: application/json' \
  --data '{
	"account": "FFF",
	"login": "admin1",
	"method": "online_score",
	"token": "995488303ad7ebe622a35c8fe8a64fffc278474d310a3346fbad64f26aeba43a83ee8dbfe1b7cd3affa4dd96d60ed31759d9aa6db92885b5afa6049c4d218333",
	"arguments": {
		"phone": 79298405555,
		"email": "wrwe@rwer",
		"first_name": "Петя",
		"last_name": "Иванок",
		"birthday": "20.04.1970",
		"gender": 2
	}
}
'
``` 