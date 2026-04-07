# backend/app/services/supabase_client.py
from __future__ import annotations
import os
from supabase import Client, create_client
from app.config import settings
from dotenv import load_dotenv

# Force load the .env file from the current directory
load_dotenv()

def get_supabase() -> Client:
    # 1. Try to get from settings
    url = settings.supabase_url or os.getenv("SUPABASE_URL")
    key = settings.supabase_key or os.getenv("SUPABASE_KEY")

    # --- TEMP DEBUG PRINT ---
    print(f"--- SUPABASE ATTEMPT ---")
    print(f"URL Found: {url}")
    print(f"Key Found (First 10 chars): {key[:10] if key else 'None'}")
    print(f"------------------------")

    if not url or not key:
        raise RuntimeError("Supabase credentials are not configured in .env")
        
    return create_client(url, key)
