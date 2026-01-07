import { createClient } from '@supabase/supabase-js';

// .env 파일에 VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY가 있어야 합니다.
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('⚠️ Supabase 환경변수가 설정되지 않았습니다 (.env 확인 필요)');
}

export const supabase = createClient(supabaseUrl!, supabaseAnonKey!);