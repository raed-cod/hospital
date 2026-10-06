from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings



engine=create_engine(settings.DATABASE_URL)

session=sessionmaker(bind=engine,autoflush=False,autocommit=False)


Base =declarative_base()

def get_db():
    db=session()
    try:
        yield db
    finally:
        db.close()