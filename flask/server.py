from hashlib import md5
from flask import Flask, jsonify, request
from flask.views import MethodView
from models import Session, Owner
from schema import CreateOwner, PatchOwner, VALIDATION_CLASS
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

app = Flask("app")


class HttpError(Exception):
    def __init__(self, status_code: int, message: dict | list | str):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HttpError)
def http_error_handler(error: HttpError):
    error_message = {"status": "error", "description": error.message}
    response = jsonify(error_message)
    response.status_code = error.status_code
    return response


def validate_json(json_data: dict, validation_model: VALIDATION_CLASS):
    try:
        model_obj = validation_model(**json_data)
        model_obj_dict = model_obj.dict(exclude_none=True)
    except ValidationError as err:
        raise HttpError(400, message=err.errors())
    return model_obj_dict


def get_owner(session: Session, owner_id: int):
    owner = session.get(Owner, owner_id)
    if owner is None:
        raise HttpError(404, message="owner doesn't exist")
    return owner


def hash_password(password: str):
    password = password.encode()
    password_hash = md5(password)
    password_hash_str = password_hash.hexdigest()
    return password_hash_str


class OwnerView(MethodView):
    def get(self, owner_id: int):
        with Session() as session:
            owner = get_owner(session, owner_id)
            return jsonify(
                {
                    "id": owner.id,
                    "owner": owner.owner,
                    "creation_time": owner.creation_time.isoformat(),
                    'heading': owner.heading,
                    'description': owner.description,

                }
            )

    def post(self):
        json_data = validate_json(request.json, CreateOwner)
        json_data["password"] = hash_password(json_data["password"])
        with Session() as session:
            user = Owner(**json_data)
            session.add(user)
            try:
                session.commit()
            except IntegrityError:
                raise HttpError(409, f'{json_data["username"]} is busy')
            return jsonify({"id": user.id})

    def patch(self, owner_id: int):
        json_data = validate_json(request.json, PatchOwner)
        if "password" in json_data:
            json_data["password"] = hash_password(json_data["password"])
        with Session() as session:
            owner = get_owner(session, owner_id)
            for field, value in json_data.items():
                setattr(owner, field, value)
            session.add(owner)
            try:
                session.commit()
            except IntegrityError:
                raise HttpError(409, f'{json_data["owner"]} is busy')
            return jsonify(
                {
                    "id": owner.id,
                    "owner": owner.owner,
                    "creation_time": owner.creation_time.isoformat(),
                }
            )

    def delete(self, owner_id: int):
        with Session() as session:
            owner = get_owner(session, owner_id)
            session.delete(owner)
            session.commit()
            return jsonify({"status": "success"})


app.add_url_rule(
    "/owner/<int:owner_id>",
    view_func=OwnerView.as_view("with_owner_id"),
    methods=["GET", "PATCH", "DELETE"],
)

app.add_url_rule("/owner/", view_func=OwnerView.as_view("create_owner"), methods=["POST"])
if __name__ == "__main__":
    app.run()