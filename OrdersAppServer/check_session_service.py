from flask import Flask, make_response, request, jsonify
from flask_restful import Resource, Api, reqparse
import psycopg2 as pgdb
import jwt
import datetime

conn = pgdb.connect(dbname="orders_app", host="localhost", user="postgres", password="88f5XX7", port="5432")

app = Flask(__name__)
api = Api()

secret_key = "ORDERS_APP_TOKEN_KEY"

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

api.add_resource(CheckSession, "/api/v1/sessions/check")
api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.104", port=5000)
