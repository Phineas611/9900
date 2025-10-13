# backend/app/database/__init__.py

# Import all models to ensure they are registered with SQLAlchemy's Base
from .models.user import User
from .models.contract import Contract
from .models.analysis_job import AnalysisJob
from .models.contract_sentence import ContractSentence
from .models.activity_log import ActivityLog