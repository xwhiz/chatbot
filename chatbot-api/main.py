from fastapi import Body, FastAPI, Header, Response, status
from typing import Annotated
from db_lifespan import db_lifespan
from fastapi.middleware.cors import CORSMiddleware

from models import User
from auth import sign_jwt, decode_jwt
from utils import hash_password

app = FastAPI(lifespan=db_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# A middleware that verify the token in the Authorization header and inject the payload into the request
@app.middleware("http")
async def verify_token(request, call_next):
    if request.url.path == "/auth/register" or request.url.path == "/auth/login":
        response = await call_next(request)
        return response

    authorization = request.headers.get("Authorization")

    if not authorization:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    token = authorization.split(" ")[1]
    payload = decode_jwt(token)

    request.state.payload = payload
    response = await call_next(request)
    return response


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/auth/register")
async def register(user: User, response: Response):
    if user.role == "admin":
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "success": False,
            "message": "Cannot create admin user",
        }

    u = await app.database["users"].find_one({"email": user.email})
    if u:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "success": False,
            "message": "User already exists, try logging in instead",
        }

    user.password = hash_password(user.password)
    result = await app.database["users"].insert_one(user.model_dump())

    if not result:
        return {"success": False, "message": "Could not create user"}

    if not result.acknowledged:
        return {"success": False, "message": "Could not create user"}

    response.status_code = status.HTTP_201_CREATED
    return {
        "success": True,
        "message": "User created successfully",
        "data": sign_jwt(
            {
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        ),
    }


@app.post("/auth/login")
async def login_user(
    response: Response, email: str = Body(...), password: str = Body(...)
):
    user = await app.database["users"].find_one({"email": email})

    if not user:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Invalid credentials"}

    if not user["password"] == hash_password(password):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Invalid credentials"}

    return {
        "success": True,
        "message": "User logged in successfully",
        "data": {
            "token": sign_jwt(
                {
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                }
            )
        },
    }


@app.post("/seed/create-admin")
async def create_admin(authorization: Annotated[str, Header()], response: Response):
    token = authorization.split(" ")[1]

    tokenPayload = decode_jwt(token)

    if "canCreateAdmin" not in tokenPayload:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    if not tokenPayload["canCreateAdmin"]:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"success": False, "message": "Unauthorized"}

    # remove current admin if there is any
    await app.database["users"].delete_many({"role": "admin"})

    # create new admin
    password = "admin"
    hashed_password = hash_password(password)

    admin = User(
        name="Admin", email="admin@chatbot.com", password=hashed_password, role="admin"
    )

    result = await app.database["users"].insert_one(admin.model_dump())

    if not result:
        return {"success": False, "message": "Could not create admin"}

    if not result.acknowledged:
        return {"success": False, "message": "Could not create admin"}

    return {"message": "Admin created successfully"}
