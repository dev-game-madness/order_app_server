from flask import Flask, make_response, request, jsonify
from flask_restful import Resource, Api, reqparse
import psycopg2 as pgdb
import jwt
import datetime

conn = pgdb.connect(dbname="orders_app", host="localhost", user="postgres", password="88f5XX7", port="5432")

app = Flask(__name__)
api = Api()

secret_key = "ORDERS_APP_TOKEN_KEY"

class UsersProfileData(Resource):
    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("profileNameDB", type=str, dest='company_name')
        parser.add_argument("profilePhoneDB", type=str, dest='phone_num')
        parser.add_argument("profileRegionDB", type=str, dest='region')
        parser.add_argument("profileCityDB", type=str, dest='city')
        parser.add_argument("profileSpecializationDB", type=str, dest='category')
        args = parser.parse_args()

        for key, value in args.items():
            if value == "":
                args[key] = None

        token = request.headers.get('Authorization')

        if not token:
            return make_response({"error": "Token not provided"}, 401)

        try:
            token = token.split(" ")[1]

            # Проверяем сессию перед выполнением запроса
            if not self.check_valid_session(token):
                return make_response({"message": "Session is invalid or expired"}, 401)

            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id = payload['user_id']

            cursor = conn.cursor()

            # Динамически формируем SQL-запрос
            set_clause = ", ".join([f"{key} = %s" for key in args])
            update_query = f"""
                UPDATE users
                SET {set_clause}
                WHERE id = %s
            """
            values = list(args.values()) + [user_id]
            cursor.execute(update_query, values)

            conn.commit()
            cursor.close()

            return make_response({"message": "Данные профиля успешно обновлены"}, 200)

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return make_response({"error": "Invalid or expired token"}, 401)
        except Exception as e:
            return make_response({"error": str(e)}, 400)

    def get(self):
        token = request.headers.get('Authorization')

        if not token:
            return make_response({"message": "Token not provided"}, 401)

        try:
            token = token.split(" ")[1]
            # Проверяем сессию перед выполнением запроса
            if not self.check_valid_session(token):
                return make_response({"message": "Session is invalid or expired"}, 401)

            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id = payload['user_id']

            cursor = conn.cursor()
            select_query = """
                SELECT email, company_name, phone_num, region, city, category
                FROM users
                WHERE id = %s
            """
            cursor.execute(select_query, (user_id,))
            user_data = cursor.fetchone()
            cursor.close()

            if user_data:
                email, company_name, phone_num, region, city, category = user_data
                return jsonify({
                    "email": email,
                    "company_name": company_name,
                    "phone_num": phone_num,
                    "region": region,
                    "city": city,
                    "category": category
                })
            else:
                return make_response({"message": "User not found"}, 404)

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return make_response({"message": "Invalid or expired token"}, 401)
        except Exception as e:
            return make_response({"error": str(e)}, 400)

    def check_valid_session(self, token):
        try:
            cursor = conn.cursor()
            query = """
                SELECT * FROM sessions
                WHERE token = %s AND out_date IS NULL
            """
            cursor.execute(query, (token,))
            session = cursor.fetchone()
            cursor.close()
            return session is not None
        except Exception as e:
            return False

api.add_resource(UsersProfileData, "/api/v1/users/profile")
api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.104", port=5003)
