-- website/db/schema.sql
-- R003 Commercial Integration Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

-- Subscriptions table (Stripe integration)
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT UNIQUE,
    stripe_price_id TEXT,
    status TEXT, -- active, canceled, past_due, trialing
    tier TEXT, -- trial, personal, professional, team
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- License Tokens (local app uses these)
CREATE TABLE IF NOT EXISTS license_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT UNIQUE NOT NULL, -- SHA-256(token)
    device_name TEXT,
    device_id TEXT,
    tier TEXT,
    expires_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usage logs
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action TEXT, -- compile, qa, embed
    tokens_used INTEGER,
    model TEXT,
    cost_cents INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Tier limits (configurable)
CREATE TABLE IF NOT EXISTS tier_limits (
    tier TEXT PRIMARY KEY,
    max_compiles INTEGER NOT NULL,
    max_qa INTEGER NOT NULL,
    allowed_models TEXT[],
    max_documents INTEGER,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Initial tier limits
INSERT INTO tier_limits (tier, max_compiles, max_qa, allowed_models, max_documents, updated_at)
VALUES
    ('trial', 5, 20, ARRAY['gpt-4o-mini'], NULL, NOW()),
    ('personal', 30, 100, ARRAY['gpt-4o-mini'], NULL, NOW()),
    ('professional', -1, -1, ARRAY['gpt-4o','claude-3.5-sonnet'], NULL, NOW())
ON CONFLICT (tier) DO NOTHING;

-- Releases (download versions)
CREATE TABLE IF NOT EXISTS releases (
    version TEXT PRIMARY KEY,
    download_url_mac TEXT,
    download_url_win TEXT,
    download_url_linux TEXT,
    release_notes TEXT,
    released_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_license_tokens_user_id ON license_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_license_tokens_token_hash ON license_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp);
