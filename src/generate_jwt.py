import os
import jwt
import datetime
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")

# Token payload
payload = {
    "sub": "uploader",
    "iat": datetime.datetime.utcnow(),
    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=10*365)
}

# Generate token
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

print("Generated JWT token:")
print(token)
