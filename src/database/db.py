import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger("Database")
Base = declarative_base()

# Variáveis globais que serão inicializadas dinamicamente
engine = None
Session = None

def get_engine():
    global engine
    if engine is None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")

        # Sanitização Profissional de URL
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        elif db_url.startswith("https://"):
            logger.warning("⚠️ DATABASE_URL detectada como HTTPS. Usando SQLite local.")
            db_url = "sqlite:///trading_bot.db"

        # Otimização para Supabase / PGBouncer
        engine = create_engine(
            db_url,
            pool_pre_ping=False,
            pool_recycle=1800
        )
    return engine

def get_session():
    global Session
    if Session is None:
        Session = sessionmaker(bind=get_engine())
    return Session()

def init_db():
    """Inicializa as tabelas do banco de dados."""
    try:
        Base.metadata.create_all(get_engine())
    except Exception as e:
        logger.error(f"Falha crítica na inicialização do DB: {e}")
        raise e

# Modelos (Exemplo de User)
from sqlalchemy import Column, String, Boolean, DateTime
import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    platform = Column(String)
    is_vip = Column(Boolean, default=False)
    subscription_date = Column(DateTime, nullable=True)
    last_interaction = Column(DateTime, default=datetime.datetime.utcnow)

def get_user(user_id):
    session = get_session()
    try:
        return session.query(User).filter(User.id == str(user_id)).first()
    finally:
        session.close()

def create_or_update_user(user_id, platform="telegram", is_vip=None):
    session = get_session()
    try:
        user = session.query(User).filter(User.id == str(user_id)).first()
        if not user:
            user = User(id=str(user_id), platform=platform)
            session.add(user)
        
        if is_vip is not None:
            user.is_vip = is_vip
            if is_vip:
                user.subscription_date = datetime.datetime.utcnow()
        
        user.last_interaction = datetime.datetime.utcnow()
        session.commit()
        return user
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao salvar usuário: {e}")
        return None
    finally:
        session.close()
