from flask import Flask
from flask_restful import Api, Resource


app = Flask(__name__)
api = Api(app)

users = {
    "luck": {
        "id": 1234,
        "xp": 0
    }
}

class Users(Resource):
    def get(self, name):
        if name in users:
            return users[name], 200
        return {}, 404

api.add_resource(Users, "/user/<string:name>")
app.run(debug=True)
