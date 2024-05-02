import json
import requests

url = "http://127.0.0.1:5000/api/v1/users"
data = {"email": "mail@mail.ru", "password": "12345"}

try:
    res = requests.post(url, json=data)
    res.raise_for_status()  # Проверить код ответа
    data = res.json()
    print(data)
except requests.exceptions.RequestException as e:
    print(f"Ошибка при выполнении запроса: {e}")
except json.JSONDecodeError as e:
    print(f"Ошибка при декодировании JSON: {e}")