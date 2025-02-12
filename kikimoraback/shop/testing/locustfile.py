from locust import HttpUser, TaskSet, task, between
import json
import uuid


class UserBehavior(TaskSet):
    def on_start(self):
        # Симуляция новой сессии: создание уникального user_id
        self.user_id = str(uuid.uuid4())
        self.cookies = {"user_id": self.user_id}

    @task
    def check_cart(self):
        # Пример данных для корзины
        data = {
            "cart": {
                "products": [
                    {"product_id": 434443626, "name": "Product 1", "price": 10, "quantity": 1}
                ],
                "total": 5
            }
        }

        # Отправка POST-запроса к endpoint /api/check_cart
        response = self.client.get(
            "api/v1/products/all",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
            cookies=self.cookies
        )

        print(f"Статус-код ответа: {response.status_code}")
        print(f"Тело ответа: {response.text}")


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(0, 1)
    host = "http://127.0.0.1:8000/"


if __name__ == "__main__":
    import os
    os.system("locust -f locustfile.py")
