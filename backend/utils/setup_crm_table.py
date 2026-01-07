import os
import sys
from pathlib import Path

# backend 폴더를 path에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config import settings
from supabase import create_client

def setup_table():
    print("🚀 Setting up crm_message_history table...")
    
    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # SQL to create table
    # Note: supabase-py client doesn't support executing raw SQL directly unless enabled on server side via RPC.
    # However, we can try to use the 'rpc' method if a function exists, or print the SQL for the user.
    # But usually, it's better to provide the SQL.
    # Wait, if we use the underlying postgrest-py, maybe? No.
    # Since we can't be sure if raw SQL execution is allowed, we will print the SQL and also try to use a direct PG connection if possible?
    # No, let's just print the SQL heavily and maybe try a dummy rpc call if "exec_sql" exists (common pattern).
    
    sql = """
    -- 1. Create Table
    CREATE TABLE IF NOT EXISTS crm_message_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
        brand TEXT NOT NULL,
        persona TEXT NOT NULL,
        intent TEXT NOT NULL,
        weather TEXT,
        beauty_profile JSONB NOT NULL, 
        message_content TEXT NOT NULL,
        query_signature TEXT
    );

    -- 2. Create Index
    CREATE INDEX IF NOT EXISTS idx_crm_history_search ON crm_message_history (brand, persona, intent);
    
    -- 3. Enable RLS (Optional but recommended)
    ALTER TABLE crm_message_history ENABLE ROW LEVEL SECURITY;
    
    -- 4. Policy (Public Read/Write for demo)
    CREATE POLICY "Public Access" ON crm_message_history FOR ALL USING (true);
    """
    
    print("\n⚠️  [IMPORTANT] Please executing the following SQL in your Supabase SQL Editor:\n")
    print("=" * 60)
    print(sql)
    print("=" * 60)
    print("\n(The python client usually cannot execute DDL commands directly related to schema modifications without a specific RPC function.)")

if __name__ == "__main__":
    setup_table()
