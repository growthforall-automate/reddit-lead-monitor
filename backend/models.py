from pydantic import BaseModel
from typing import Optional, List


class Lead(BaseModel):
    id: Optional[str] = None
    name: str = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    company: Optional[str] = ""
    role: Optional[str] = ""
    value: Optional[str] = ""
    source: Optional[str] = "Manual"
    stage: Optional[str] = "new"
    notes: Optional[str] = ""
    followUp: Optional[str] = ""


class LeadImport(BaseModel):
    leads: List[Lead]


class BrainFile(BaseModel):
    filename: Optional[str] = None
    content: str


class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_username: Optional[str] = None
    reddit_password: Optional[str] = None
    reddit_user_agent: Optional[str] = None
    reddit_subreddits: Optional[str] = None
    reddit_min_score: Optional[str] = None
    reddit_scan_limit: Optional[str] = None
