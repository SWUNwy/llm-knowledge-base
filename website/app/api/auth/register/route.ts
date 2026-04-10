// website/app/api/auth/register/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne, User } from '@/lib/db';
import { hashPassword, signAccessToken } from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Email and password are required' } },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Password must be at least 8 characters' } },
        { status: 400 }
      );
    }

    // Check if user exists
    const existing = await queryOne<User>(
      'SELECT id FROM users WHERE email = $1',
      [email]
    );

    if (existing) {
      return NextResponse.json(
        { error: { code: 'AUTH_EMAIL_EXISTS', message: 'Email already registered' } },
        { status: 409 }
      );
    }

    // Create user
    const passwordHash = await hashPassword(password);
    const user = await queryOne<User>(
      `INSERT INTO users (email, password_hash)
       VALUES ($1, $2)
       RETURNING id, email, created_at`,
      [email, passwordHash]
    );

    if (!user) {
      throw new Error('Failed to create user');
    }

    // Create trial subscription
    await query(
      `INSERT INTO subscriptions (user_id, status, tier, current_period_start, current_period_end)
       VALUES ($1, 'trialing', 'trial', NOW(), NOW() + INTERVAL '14 days')`,
      [user.id]
    );

    // Sign JWT
    const token = signAccessToken({ sub: user.id, email: user.email, tier: 'trial' });

    return NextResponse.json({
      access_token: token,
      user: { id: user.id, email: user.email },
      redirect_to: '/pricing' // Will go to Stripe next
    });

  } catch (error) {
    console.error('Registration error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Registration failed' } },
      { status: 500 }
    );
  }
}
