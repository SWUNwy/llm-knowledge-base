// website/lib/db.ts
import { Pool } from 'pg';

if (!process.env.DATABASE_URL) {
  throw new Error('DATABASE_URL environment variable is not set');
}

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

export interface User {
  id: string;
  email: string;
  password_hash: string;
  created_at: Date;
  last_login_at: Date | null;
}

export interface Subscription {
  id: string;
  user_id: string;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  stripe_price_id: string | null;
  status: string;
  tier: string;
  current_period_start: Date | null;
  current_period_end: Date | null;
  cancel_at_period_end: boolean;
  created_at: Date;
  updated_at: Date;
}

export interface LicenseToken {
  id: string;
  user_id: string;
  token_hash: string;
  device_name: string | null;
  device_id: string | null;
  tier: string;
  expires_at: Date | null;
  last_seen_at: Date | null;
  created_at: Date;
}

export interface UsageLog {
  id: string;
  user_id: string;
  action: string;
  tokens_used: number | null;
  model: string | null;
  cost_cents: number | null;
  timestamp: Date;
}

export interface TierLimits {
  tier: string;
  max_compiles: number;
  max_qa: number;
  allowed_models: string[];
  max_documents: number | null;
  updated_at: Date;
}

export async function query<T>(text: string, params?: any[]): Promise<T[]> {
  const client = await pool.connect();
  try {
    const result = await client.query(text, params);
    return result.rows as T[];
  } finally {
    client.release();
  }
}

export async function queryOne<T>(text: string, params?: any[]): Promise<T | null> {
  const rows = await query<T>(text, params);
  return rows[0] || null;
}
