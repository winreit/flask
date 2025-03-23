import hashlib
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models import Owner
from schema import CreateOwner, PatchOwner, VALIDATION_CLASS
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

async def index(request):
    return web.Response(text="Hello, world")

app = web.Application()

async def init_db(app):
    engine = create_async_engine("postgresql+asyncpg://user:password@localhost/dbname")
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    app['db'] = async_session

async def close_db(app):
    await app['db'].close()

app.on_startup.append(init_db)
app.on_cleanup.append(close_db)

class HttpError(web.HTTPException):
    def __init__(self, status_code: int, message: dict | list | str):
        super().__init__(text=message)
        self.status_code = status_code

async def validate_json(json_data: dict, validation_model: VALIDATION_CLASS):
    try:
        model_obj = validation_model(**json_data)
        model_obj_dict = model_obj.dict(exclude_none=True)
    except ValidationError as err:
        raise HttpError(400, message=str(err.errors()))
    return model_obj_dict

async def get_owner(session: AsyncSession, owner_id: int):
    owner = await session.get(Owner, owner_id)
    if owner is None:
        raise HttpError(404, message="owner doesn't exist")
    return owner

def hash_password(password: str):
    password = password.encode()
    password_hash = hashlib.md5(password)
    password_hash_str = password_hash.hexdigest()
    return password_hash_str

class OwnerView(web.View):
    async def get(self):
        owner_id = int(self.request.match_info['owner_id'])
        async with self.request.app['db']() as session:
            owner = await get_owner(session, owner_id)
            return web.json_response({
                "id": owner.id,
                "owner": owner.owner,
                "creation_time": owner.creation_time.isoformat(),
                'heading': owner.heading,
                'description': owner.description,
            })

    async def post(self):
        json_data = await self.request.json()
        json_data = await validate_json(json_data, CreateOwner)
        json_data["password"] = hash_password(json_data["password"])
        async with self.request.app['db']() as session:
            owner = Owner(**json_data)
            session.add(owner)
            try:
                await session.commit()
            except IntegrityError:
                raise HttpError(409, f'{json_data["owner"]} is busy')
            return web.json_response({"id": owner.id})

    async def patch(self):
        owner_id = int(self.request.match_info['owner_id'])
        json_data = await self.request.json()
        json_data = await validate_json(json_data, PatchOwner)
        if "password" in json_data:
            json_data["password"] = hash_password(json_data["password"])
        async with self.request.app['db']() as session:
            owner = await get_owner(session, owner_id)
            for field, value in json_data.items():
                setattr(owner, field, value)
            session.add(owner)
            try:
                await session.commit()
            except IntegrityError:
                raise HttpError(409, f'{json_data["owner"]} is busy')
            return web.json_response({
                "id": owner.id,
                "owner": owner.owner,
                "creation_time": owner.creation_time.isoformat(),
            })

    async def delete(self):
        owner_id = int(self.request.match_info['owner_id'])
        async with self.request.app['db']() as session:
            owner = await get_owner(session, owner_id)
            await session.delete(owner)
            await session.commit()
            return web.json_response({"status": "success"})

app.router.add_route('*', '/owner/{owner_id}', OwnerView)
app.router.add_route('POST', '/owner/', OwnerView)

if __name__ == "__main__":
    web.run_app(app)