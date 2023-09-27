from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

################################### Create a PostgreSQL database connection################################
DATABASE_URL = "postgresql://username:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

############################## User table in PostgreSQL3 ###################################

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone = Column(String)
    profile_id = Column(Integer, ForeignKey("profiles.id"))

######################################### Create a Profile table in PostgreSQL#############################
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    profile_picture = Column(String)
    user = relationship("User", back_populates="profile")

Base.metadata.create_all(bind=engine)

app = FastAPI()

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    phone: str
    profile_picture: str

@app.post("/register/")
def register_user(user: UserCreate):
    ##################################### Check if the email and phone already exist in PostgreSQL########################
    db = SessionLocal()
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    ###################################Create a new user in PostgreSQL###############################
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    ###################################### Create a new profile in PostgreSQL#############################
    db_profile = Profile(profile_picture=user.profile_picture)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    ############################################ Update the user's profile_id###############################
    db_user.profile_id = db_profile.id
    db.commit()

    return db_user

@app.get("/user/{user_id}/")
def get_user(user_id: int):
    ############################################# Retrieve user details and profile from PostgreSQL################################
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user": user, "profile": user.profile}
