from flask import Flask, make_response, request, jsonify
from flask_restful import Resource, Api, reqparse
import psycopg2 as pgdb
import jwt
import datetime

conn = pgdb.connect(dbname="orders_app", host="localhost", user="postgres", password="88f5XX7", port="5432")

app = Flask(__name__)
api = Api()

secret_key = "ORDERS_APP_TOKEN_KEY"
class CheckConnection(Resource):
    def head(self):
        try:
            return make_response({"message": "Сервер доступен"}, 200)
        except Exception as e:
            return make_response({"error": str(e)}, 500)

api.add_resource(CheckConnection, "/api/v1/connection/check")
api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.104", port=5001)
