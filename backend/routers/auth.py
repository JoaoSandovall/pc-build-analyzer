from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
from security import verify_password, create_access_token, get_password_hash
from dependencies import get_db
from rate_limiter import limiter

# Cria um mini-aplicativo apenas para rotas que começam com /auth
router = APIRouter(prefix="/auth", tags=["Autenticação"])

class UserCreate(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128, description="A senha deve ter entre 8 e 128 caracteres")

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
def register_user(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado.")
    
    hashed_password = get_password_hash(user.senha)
    novo_usuario = models.User(email=user.email.lower(), senha_hash=hashed_password)
    
    db.add(novo_usuario)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email já cadastrado.") from exc
    db.refresh(novo_usuario)
    
    return {"id": novo_usuario.id, "email": novo_usuario.email}

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username.lower()).first()
    
    if not user or not verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
