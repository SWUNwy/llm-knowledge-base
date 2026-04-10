# R003 SaaS Deployment Guide

## Prerequisites

1. PostgreSQL database (Supabase or Neon)
2. Stripe account with products configured
3. Vercel account for website deployment
4. Domain name configured

## Database Setup

1. Create database at Supabase/Neon
2. Run migration: `psql $DATABASE_URL -f website/db/schema.sql`
3. Verify tables created

## Stripe Setup

1. Create products in Stripe Dashboard:
   - Personal: monthly and yearly pricing
   - Professional: monthly and yearly pricing

2. Copy webhook secret and add to environment variables

3. Configure webhook endpoint: `https://your-domain.com/api/stripe/webhook`

## Website Deployment (Vercel)

1. Connect GitHub repo to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy from `website/` directory

## Local App Distribution

1. Build executables:
   - Mac: `pyinstaller --onefile backend/src/main.py`
   - Win: `pyinstaller --onefile --windowed backend/src/main.py`

2. Upload to website releases table

## Verification Checklist

- [ ] User can register at /register
- [ ] Registration redirects to Stripe checkout
- [ ] After payment, user sees dashboard
- [ ] Local app can login with email/password
- [ ] License verification works
- [ ] LLM proxy streams responses
- [ ] Usage tracking works
