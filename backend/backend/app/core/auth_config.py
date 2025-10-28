import os

SECRET_KEY = os.getenv("UPLIFT_SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("UPLIFT_TOKEN_MINUTES", "120"))
