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

def reset_db():
    """Limpa engine/sessão para permitir nova inicialização (testes ou reload)."""
    global engine, Session
    engine = None
    Session = None
    logger.info("Conexão com o banco de dados resetada.")

def get_engine():
    global engine
    if engine is None:
        # Somente SQLite. Caminho: arquivo ou URL completa sqlite:///...
        raw = os.getenv("SQLITE_DATABASE", "trading_bot.db")
        if raw.startswith("sqlite:"):
            db_url = raw
        else:
            db_url = f"sqlite:///{raw}"
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
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
