import json


with open("users.json") as users:
    USERS = json.load(users)["users"]
