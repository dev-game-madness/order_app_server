from flask import Flask, make_response, request, jsonify
from flask_restful import Resource, Api, reqparse
import psycopg2 as pgdb
import jwt
import datetime

conn = pgdb.connect(dbname="orders_app", host="localhost", user="postgres", password="88f5XX7", port="5432")

app = Flask(__name__)
api = Api()

secret_key = "ORDERS_APP_TOKEN_KEY"

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
                    cursor.execute(
                        f"INSERT INTO users (email, password, fullreg, reg_date) VALUES ('{user_email}', {user_password}, False, NOW())")
                    conn.commit()
                    cursor.close()
                    return make_response({"OK": "Пользователь создан"}, 201)
                except Exception as e:
                    return make_response({"error": str(e)}, 400)
            else:
                if user_email == email_db[0]:
                    return make_response({"error": "Пользователь с этим Email уже существует"}, 409)
                else:
                    return make_response({"error": "Необработанная ошибка"}, 400)
        except Exception as e:
            return make_response({"error": str(e)}, 400)

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

class CheckSession(Resource):

    def get(self):

        def check_session(token):
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

        token = request.headers.get('Authorization')
        if not token:
            return make_response({"message": "Token not provided"}, 401)
        else:
            try:
                token = token.split(" ")[1]
                if check_session(token):
                    return make_response({"message": "Session is valid"}, 200)
                else:
                    return make_response({"message": "Session is invalid or expired"}, 401)
            except Exception as e:
                return make_response({"error": str(e)}, 400)

class UsersLogout(Resource):

    def put(self):

        def close_session(token):
            try:
                cursor = conn.cursor()
                query = """
                    UPDATE sessions SET out_date = CURRENT_TIMESTAMP 
                    WHERE token = %s 
                    AND out_date IS NULL;
                """
                cursor.execute(query, (token,))
                conn.commit()
                cursor.close()
            except Exception as e:
                return False

        token = request.headers.get('Authorization')
        if not token:
            return make_response({"message": "Невалидный токен"}, 401)
        else:
            try:
                token = token.split(" ")[1]
                if close_session(token):
                    return make_response({"message": "Сессия завершена"}, 200)
                else:
                    return make_response({"message": "Сессия не завершена"}, 401)
            except Exception as e:
                return make_response({"error": str(e)}, 400)

class CheckConnection(Resource):
    def head(self):
        try:
            return make_response({"message": "Сервер доступен"}, 200)
        except Exception as e:
            return make_response({"error": str(e)}, 500)


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

class MyOrders(Resource):
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
                            FROM orders WHERE user_id = %s AND order_close IS NULL
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

class Orders(Resource):
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
                FROM orders WHERE order_close IS NULL
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
                return make_response({"message": "Orders not found"}, 404)

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


api.add_resource(UsersRegistration, "/api/v1/users/reg")
api.add_resource(UsersProfileData, "/api/v1/users/profile")
api.add_resource(UsersLogin, "/api/v1/users/log")
api.add_resource(UsersLogout, "/api/v1/users/logout")
api.add_resource(CheckSession, "/api/v1/sessions/check")
api.add_resource(CheckConnection, "/api/v1/connection/check")
api.add_resource(NewOrders, "/api/v1/orders/create")
api.add_resource(Orders, "/api/v1/orders/all")
api.add_resource(MyOrders, "/api/v1/orders/myorders")
api.add_resource(MyArchiveOrders, "/api/v1/orders/myarchiveorders")
api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.104", port=5000)
