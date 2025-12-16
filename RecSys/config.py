import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Supabase Settings
    SUPABASE_URL: str = "https://upahiamvvoxrzjqpqrhk.supabase.co"
    SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVwYWhpYW12dm94cnpqcXBxcmhrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUzNDgwNTgsImV4cCI6MjA4MDkyNDA1OH0.e13FP0bsjhSD93kGN72Pq3B7nnNmewBts9AQHbxuftk"

    class Config:
        env_file = ".env"

settings = Settings()
