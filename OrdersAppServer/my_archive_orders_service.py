from flask import Flask, make_response, request, jsonify
from flask_restful import Resource, Api, reqparse
import psycopg2 as pgdb
import jwt
import datetime

conn = pgdb.connect(dbname="orders_app", host="localhost", user="postgres", password="88f5XX7", port="5432")

app = Flask(__name__)
api = Api()

secret_key = "ORDERS_APP_TOKEN_KEY"

class MyArchiveOrders(Resource):
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
                            SELECT id, order_name, "order", category, subcategory, order_deadline, order_budget, TO_CHAR(order_create , 'DD.MM.YYYY HH:mm:SS'), order_region, order_city
                            FROM orders WHERE user_id = %s AND order_close IS NOT NULL
                        """
            cursor.execute(select_query, (user_id,))
            my_orders_data = cursor.fetchall()
            cursor.close()

            if my_orders_data:
                orders = []
                for order in my_orders_data:
                    order_dict = {
                        "id": order[0],
                        "order_name": order[1],
                        "order": order[2],
                        "category": order[3],
                        "subcategory": order[4],
                        "order_deadline": order[5],
                        "order_budget": order[6],
                        "order_create": order[7],
                        "order_region": order[8],
                        "order_city": order[9]
                    }
                    orders.append(order_dict)

                return jsonify({"orders": orders})
            else:
                return make_response({"error": "Orders not found"}, 404)

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

api.add_resource(MyArchiveOrders, "/api/v1/orders/myarchiveorders")
api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.104", port=5009)
