import os

os.environ.setdefault(
    "DATABASE_URL",
    "mysql+aiomysql://root:wj123456@127.0.0.1:3306/pocket_farm?charset=utf8mb4",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret")
