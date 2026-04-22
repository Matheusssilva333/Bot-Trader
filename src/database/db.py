from sqlalchemy import create_all, Column, Integer, String, Boolean, DateTime, create_engine
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

engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///trading_bot.db"))
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
