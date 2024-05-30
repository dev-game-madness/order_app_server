from flask import Flask, make_response, request, jsonify
from flask_restful import Resource, Api, reqparse
import psycopg2 as pgdb
import jwt
import datetime

conn = pgdb.connect(dbname="orders_app", host="localhost", user="postgres", password="88f5XX7", port="5432")

app = Flask(__name__)
api = Api()

secret_key = "ORDERS_APP_TOKEN_KEY"

class NewOrders(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True)
        parser.add_argument("mainCategory", type=str, required=True)
        parser.add_argument("subCategory", type=str, required=True)
        parser.add_argument("date", type=int, required=True)
        parser.add_argument("budget", type=int, required=True)
        parser.add_argument("description", type=str)
        args = parser.parse_args()

        token = request.headers.get('Authorization')
        if not token:
            return make_response({"error": "Token not provided"}, 401)

        try:
            token = token.split(" ")[1]

            if not self.check_valid_session(token):
                return make_response({"message": "Session is invalid or expired"}, 401)

            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id = payload['user_id']

            cursor = conn.cursor()
            insert_query = """
                INSERT INTO orders (user_id, order_name, category, subcategory, order_deadline, order_budget, "order", order_create)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(insert_query, (user_id, args["name"], args["mainCategory"],
                                         args["subCategory"], args["date"], args["budget"],
                                         args["description"]))
            conn.commit()
            cursor.close()

            return make_response({"message": "Заказ успешно создан"}, 201)

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return make_response({"error": "Invalid or expired token"}, 401)
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

api.add_resource(NewOrders, "/api/v1/orders/create")
api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.104", port=5006)
