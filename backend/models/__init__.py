from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all your models here
from backend.models.user import User
# Add your other models if they exist
# from .conversation import Conversation

__all__ = ["Base", "User"]