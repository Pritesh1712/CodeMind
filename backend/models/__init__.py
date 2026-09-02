# models/__init__.py
# Makes the models directory a Python package.
# Import all models here so SQLModel can discover them for table creation.

from .repository import Repository, RepositoryStatus
from .chat import Chat, Message
from .schemas import *
