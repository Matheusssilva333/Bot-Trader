from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    platform_id = Column(String, unique=True) # Discord or Telegram ID
    platform = Column(String) # 'telegram' or 'discord'
    is_vip = Column(Boolean, default=False)
    payment_date = Column(DateTime)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.now)


db_url = os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")

# Sanitização Profissional de URL (Suporte total ao Supabase/Render)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
elif "supabase.co" in db_url and db_url.startswith("https://"):
    print("⚠️ AVISO: Você usou a URL da API do Supabase. Use a Connection String (URI) da aba Database Settings.")
    db_url = "sqlite:///trading_bot.db"

# Configuração de Engine otimizada para Supabase (evita quedas de conexão)
engine = create_engine(
    db_url,
    pool_pre_ping=True, # Verifica se a conexão está viva antes de usar
    pool_recycle=3600    # Recicla conexões a cada hora
)
Session = sessionmaker(bind=engine)



def init_db():
    Base.metadata.create_all(engine)

def get_user(platform_id: str):
    session = Session()
    user = session.query(User).filter_by(platform_id=platform_id).first()
    session.close()
    return user

def create_or_update_user(platform_id: str, platform: str, is_vip: bool = False):
    session = Session()
    user = session.query(User).filter_by(platform_id=platform_id).first()
    if not user:
        user = User(platform_id=platform_id, platform=platform, is_vip=is_vip)
        session.add(user)
    else:
        user.is_vip = is_vip
        if is_vip:
            user.payment_date = datetime.datetime.now()
            user.expiry_date = user.payment_date + datetime.timedelta(days=30)
    session.commit()
    session.close()
