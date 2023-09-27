from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pymongo import MongoClient
from pydantic import BaseModel

############################################ Create a PostgreSQL database connection############################
DATABASE_URL = "postgresql://username:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

####################################### Create a MongoDB connection################################
mongo_client = MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client["mydatabase"]
mongo_collection = mongo_db["user_profiles"]

Base = declarative_base()

######################################### Create a User table in PostgreSQL #############################
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone = Column(String)

Base.metadata.create_all(bind=engine)

app = FastAPI()

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    phone: str

class UserProfile(BaseModel):
    profile_picture: str

@app.post("/register/")
def register_user(user: UserCreate):
    ############################################## Check if the email already exists in PostgreSQL################
    db = SessionLocal()
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    ##################################### Create a new user in PostgreSQL#######################################
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    ###################################### Store profile picture in MongoDB################################
    profile_data = {"profile_picture": user.profile_picture}
    mongo_collection.insert_one(profile_data)

    return db_user

@app.get("/user/{user_id}/")
def get_user(user_id: int):
    ##################################### Retrieve user details from PostgreSQL###########################
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ################################ Retrieve profile picture from MongoDB#############################
    profile_data = mongo_collection.find_one({})
    user_profile = UserProfile(**profile_data)

    return {"user": user, "profile": user_profile}
