from fastapi import FastAPI,Response,HTTPException,Request,status,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from astrapy import DataAPIClient
from dotenv import load_dotenv
from utill import create_access_token,verify_refresh_token,hashedpassword,VerifyHashed,verify_access_token
import os
from model import Admin,LoginData
load_dotenv()
import math
from apscheduler.schedulers.asyncio import AsyncIOScheduler

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_TOKEN = os.getenv("DATABASE_TOKEN")
# FRONTEND_URL = os.getenv("FRONTEND_URL")
FRONTEND_URL1 = os.getenv("FRONTEND_URL1")
FRONTEND_URL2 = os.getenv("FRONTEND_URL2")
FRONTEND_URL3 = os.getenv("FRONTEND_URL3")
# Initialize the client
client = DataAPIClient(DATABASE_TOKEN)
db = client.get_database_by_api_endpoint(
  DATABASE_URL
)

# print(f"Connected to Astra DB: {db.list_collection_names()}")
kyc_data_collection=db.create_collection("user_kyc_data")
admin_data=db.create_collection("admin_data")






app = FastAPI()
scheduler = AsyncIOScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL1,FRONTEND_URL2,FRONTEND_URL3],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)


# cron
def ping_db():
    data=kyc_data_collection.find().to_list()
    print("Pinging database to prevent hibernation")
    


# @app.on_event("startup")
# def start_scheduler():
#     scheduler.add_job(ping_db, "interval", hours=12)
#     scheduler.start()

# Dependency to to authenticate admin




security = HTTPBearer()

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # print("Credentials received:", credentials)
    token = credentials.credentials
    payload, expired = verify_access_token(token)

    if expired:
        admin=admin_data.find_one({"_id":payload.get("_id")})
        if not admin:
            return {"status":"error","message":"Admin not found"}
        refresh_payload=verify_refresh_token(admin["refresh_token"])
        if not refresh_payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        del admin["refresh_token"]
        access_token= create_access_token(admin,expires_delta=15)
        return {"token":access_token, "message": "Login successful","status_code": status.HTTP_200_OK}

    if not payload:
        return { "message": "No token","status_code": status.HTTP_401_UNAUTHORIZED}
        

    return payload



def chunk_base64_string(b64_string, chunk_size=4000):  # 4000 bytes < 8 KB
    return [b64_string[i:i + chunk_size] for i in range(0, len(b64_string), chunk_size)]

@app.post("/submit_kyc")
async def submit_kyc(data: dict):
    try:
        # Check for profile_picture or signature fields
        for field in ["profile_picture", "signature","utility_bill","means_of_id"]:
            if field in data and data[field]:
                # Split large base64 string into chunks
                chunks = chunk_base64_string(data[field], chunk_size=4000)
                data[field] = chunks  # Store as list of chunks

        # Store data in your DB (here just appending to a list)
        kyc_data_collection.insert_one(data)

        print("Received KYC data:", data)
        return {"status": "success", "message": "KYC data submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Create admin endpoint
@app.post("/create_admin")
async def create_admin(admin: Admin):
    data = admin.dict()
    data["password"] = hashedpassword(data["password"])
    check_admin = admin_data.find_one({"email": data["email"]})
    if check_admin:
        return {"status": "error", "message": "Admin already exists"}
    admin_data.insert_one(data)
    return {"status": "success", "message": "Admin created successfully"}


# delete user kyc
@app.get("/delete_kyc/{id}")
async def delete_kyc(id:str):
     kyc_data_collection.find_one_and_delete({"_id":id})
     return {"message":"Data Deleted Successfully","status":"success"}

# Delete admin endpoint

@app.delete("/delete_admin/{admin_email}")
async def delete_admin(admin_email: str):
    result = admin_data.delete_one({"email": admin_email})
    if result.deleted_count == 0:
        return {"status": "error", "message": "Admin not found"}
    return {"status": "success", "message": "Admin deleted successfully"}

# Login endpoint


@app.post("/login") 
async def login(data: LoginData,response: Response): 
    data = data.dict() 
    email = data["email"] 
    admin_email =admin_data.find_one({"email":email}) 
    del admin_email["refresh_token"] 
    if admin_email: 
        if VerifyHashed(admin_email["password"],data["password"]): 
                print("Password verified successfully")
                refresh_token=create_access_token(admin_email,expires_delta=60*24*7) 
                # refresh token valid for 7 days 
                admin_data.find_one_and_update({"email":email},{"$set":{"refresh_token":refresh_token}}) 
                access_token=create_access_token(admin_email,expires_delta=15) 
                
                return {"userId": str(admin_email["_id"]),"token":access_token, "message": "Login successful","status": "success"} 
                
        else:   
                return {"status_code": status.HTTP_401_UNAUTHORIZED, "detail": "Invalid password"}
                
    else: 
            
            return {"status": "error", "message": "Invalid admin email"} 




# Protected route example
@app.post("/admin_dashboard")
async def admin_dashboard(payload: dict = Depends(get_current_admin)):
    admin_id = payload.get("_id")
    all_kyc_data = kyc_data_collection.find().to_list()

    return {
         "status": "success",
        "admin_id": admin_id,
        "kyc_data": all_kyc_data
    }