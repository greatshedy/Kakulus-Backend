from dotenv import load_dotenv
from argon2 import PasswordHasher
import os
from jose import JWTError, jwt,ExpiredSignatureError
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import secrets
import smtplib

load_dotenv()

ALGORITHM = os.getenv("ALGORITHM")
SECRET_KEY = os.getenv("SECRET_KEY")

def create_access_token(data:dict, expires_delta: int):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=expires_delta)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


ph=PasswordHasher()
def hashedpassword(password):
    hashed=ph.hash(password)
    return hashed


def VerifyHashed(hashedpassword,password):
    value=ph.verify(hashedpassword,password)
    return value


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload,False  # valid token
    except ExpiredSignatureError:
        # 🔥 Decode again but ignore expiration
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False}
        )
        expired=True
        return payload,expired # expired but usable
    except JWTError:
        return None,False  # invalid token
    

def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload # expired but usable
    except JWTError:
        return None  # invalid token


    
# # function to generate otp
# def generate_otp():
#     """Generate a secure 6-digit OTP code."""
#     return str(secrets.randbelow(1000000)).zfill(6)

