from flask import Flask, make_response, request, jsonify
from flask_restful import Resource, Api, reqparse
import psycopg2 as pgdb
import jwt
import datetime

conn = pgdb.connect(dbname="orders_app", host="localhost", user="postgres", password="88f5XX7", port="5432")

app = Flask(__name__)
api = Api()

secret_key = "ORDERS_APP_TOKEN_KEY"

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

api.add_resource(UsersLogout, "/api/v1/users/logout")
api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.104", port=5002)
