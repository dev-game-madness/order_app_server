from flask import Flask, make_response
from flask_restful import Resource, Api, reqparse
import psycopg2 as pgdb

conn = pgdb.connect(dbname="orders_app", host="localhost", user="postgres", password="88f5XX7", port="5432")

# "http://127.0.0.1:5000/api/v1/users"

app = Flask(__name__)
api = Api()


class UsersRegistration(Resource):
    def post(self):

        parser = reqparse.RequestParser()
        parser.add_argument("email", type=str, required=True)
        parser.add_argument("password", type=str, required=True)
        args = parser.parse_args()

        user_email = args["email"]
        user_password = args["password"]

        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT email FROM users WHERE email = '{user_email}'")
            email_db = cursor.fetchone()
            cursor.close()
            if email_db is None:
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"INSERT INTO users (email, password) VALUES ('{user_email}', {user_password})")
                    conn.commit()
                    cursor.close()
                    return make_response({"OK": "Пользователь создан"}, 201)
                except Exception as e:
                    return make_response({"create_error": str(e)}, 400)
            else:
                if user_email == email_db[0]:
                    return make_response({"error": "Пользователь с этим Email уже существует"}, 409)
                else:
                    return make_response({"validate_error": "Необработанная ошибка"}, 400)
        except Exception as e:
            return make_response({"validate_error": str(e)}, 400)


class UsersLogin(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("email", type=str, required=True)
        parser.add_argument("password", type=str, required=True)
        args = parser.parse_args()

        user_email = args["email"]
        user_password = args["password"]

        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT password FROM users WHERE email = '{user_email}' AND password = '{user_password}'")
            password_db = cursor.fetchone()
            print(password_db)
            cursor.close()
        except Exception as e:
            return make_response({"error": str(e)}, 400)


api.add_resource(UsersRegistration, "/api/v1/users/reg")
api.add_resource(UsersLogin, "/api/v1/users/log")
api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.104", port=5000)