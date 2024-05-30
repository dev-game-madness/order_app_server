from flask import Flask, make_response, request, jsonify
from flask_restful import Resource, Api, reqparse
import psycopg2 as pgdb
import jwt
import datetime

conn = pgdb.connect(dbname="orders_app", host="localhost", user="postgres", password="88f5XX7", port="5432")

app = Flask(__name__)
api = Api()

secret_key = "ORDERS_APP_TOKEN_KEY"


class UsersLogin(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("email", type=str, required=True)
        parser.add_argument("password", type=str, required=True)
        args = parser.parse_args()

        user_email = args["email"]
        user_password = args["password"]

        def generate_jwt(user_id, email):
            payload = {
                "user_id": user_id,
                "email": email,
                "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
            }
            encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256")
            return encoded_jwt

        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT id, email, password FROM users WHERE email = '{user_email}'")
            user_data = cursor.fetchone()
            cursor.close()

            if user_data is None:
                return make_response({"error": "Пользователя с таким Email не существует"}, 409)
            else:
                user_id, email, password = user_data
                if user_password == password:
                    token = generate_jwt(user_id, email)

                    try:
                        cursor = conn.cursor()
                        update_query = """
                                                UPDATE sessions
                                                SET out_date = CURRENT_TIMESTAMP
                                                WHERE user_id = %s AND out_date IS NULL AND token != %s
                                            """
                        cursor.execute(update_query,(user_id, token))
                        conn.commit()
                        cursor.close()
                    except Exception as e:
                        return make_response({"error": f"Ошибка при завершении предыдущих сессий: {e}"}, 400)

                    try:
                        cursor = conn.cursor()
                        insert_query = """
                                    INSERT INTO sessions (user_id, token, login_date)
                                    VALUES (%s, %s, NOW())
                                """
                        cursor.execute(insert_query, (user_id, token))
                        conn.commit()
                        cursor.close()
                        return make_response({"token": token}, 200)
                    except Exception as e:
                        return make_response({"error": str(e)}, 400)
                else:
                    return make_response({"error": "Неверный логин или пароль"}, 401)
        except Exception as e:
            return make_response({"error": str(e)}, 400)

api.add_resource(UsersLogin, "/api/v1/users/log")
api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.104", port=5004)
