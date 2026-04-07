from __future__ import annotations

from supabase import Client, create_client

from app.config import settings


def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("Supabase credentials are not configured.")
    return create_client(settings.supabase_url, settings.supabase_key)
