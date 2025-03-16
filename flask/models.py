from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func

engine = create_engine("postgresql://postgres:postgres@127.0.0.1:5431/flask1")
Session = sessionmaker(bind=engine)
Base = declarative_base(bind=engine)


class Owner(Base):
    __tablename__ = "app_owners"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    creation_time = Column(DateTime, server_default=func.now())
    heading = Column(String)
    description = Column(String)


Base.metadata.create_all()