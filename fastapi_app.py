from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from jwt import encode, decode  # Updated import from PyJWT
import hashlib
import json
import os
from src.helper import *
from src.prompt import *

# ---------------- Configuration ----------------
SECRET_KEY = "codebasics"  # Use a more secure key in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="ChatBot Pro API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ---------------- Utility Functions ----------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str):
    return hash_password(plain_password) == hashed_password

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- User Management ----------------
class UserManager:
    def __init__(self, db_file="users.json"):
        self.db_file = db_file
        self.users = self.load_users()
    
    def load_users(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_users(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def register_user(self, username: str, department: str, email: str, password: str, full_name: str):
        if username in self.users:
            return False, "Username already exists"
        if any(user.get('email') == email for user in self.users.values()):
            return False, "Email already registered"
        
        self.users[username] = {
            'email': email,
            'department': department,
            'password': hash_password(password),
            'full_name': full_name,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        self.save_users()
        return True, "Registration successful"
    
    def authenticate_user(self, username: str, password: str):
        if username not in self.users:
            return False, "User not found"
        if self.users[username]['password'] != hash_password(password):
            return False, "Invalid password"
        
        self.users[username]['last_login'] = datetime.now().isoformat()
        self.save_users()
        return True, "Login successful"
    
    def get_user_info(self, username: str):
        return self.users.get(username, {})

user_manager = UserManager()

# ---------------- Pydantic Models ----------------
class RegisterData(BaseModel):
    full_name: str
    username: str
    department: str
    email: EmailStr
    password: str
    confirm_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginData(BaseModel):
    username: str
    password: str

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    context: Optional[Any] = None

# ---------------- Dummy Chat Logic ----------------
# def answer(question: str, input_department: str):
#     Dummy response: simply echo the question and department.
#     response = f"Echo: {question} from {input_department} support."
#     context = {"dummy_context": True}
#     return response, context

# ---------------- Dependency: Get Current User ----------------
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials."
    )
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    user = user_manager.get_user_info(username)
    if not user:
        raise credentials_exception
    return {"username": username, "department": user.get("department")}

# ---------------- Chat History Storage ----------------
chat_histories: Dict[str, List[Dict[str, Any]]] = {}

# ---------------- Endpoints ----------------
@app.post("/register", response_model=Token)
async def register(data: RegisterData):
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
    
    success, msg = user_manager.register_user(data.username, data.department, data.email, data.password, data.full_name)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    access_token = create_access_token(data={"sub": data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    success, msg = user_manager.authenticate_user(form_data.username, form_data.password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatMessage, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    department = current_user["department"]
    
    history = chat_histories.get(username, [])
    history.append({"role": "user", "content": chat.message, "timestamp": datetime.now().strftime("%I:%M %p")})
    
    response_text, context = answer(chat.message, department)
    
    history.append({"role": "assistant", "content": response_text, "timestamp": datetime.now().strftime("%I:%M %p"), "context": context})
    chat_histories[username] = history
    
    return {"response": response_text, "context": context}

@app.get("/chat/history")
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    return chat_histories.get(username, [])

@app.get("/")
async def root():
    return {"message": "Welcome to the ChatBot Pro API!"}