// website/app/api/auth/login/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne, User } from '@/lib/db';
import { verifyPassword, signAccessToken, signLicenseToken } from '@/lib/auth';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const { email, password, device_name, device_id } = await request.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Email and password are required' } },
        { status: 400 }
      );
    }

    // Get user with subscription
    const user = await queryOne<User & {tier: string}>(
      'SELECT u.*, s.tier FROM users u LEFT JOIN subscriptions s ON s.user_id = u.id WHERE u.email = $1',
      [email]
    );

    if (!user) {
      return NextResponse.json(
        { error: { code: 'AUTH_INVALID_CREDENTIALS', message: 'Invalid email or password' } },
        { status: 401 }
      );
    }

    // Verify password (user object has password_hash from query)
    const userWithHash = await queryOne<{password_hash: string}>(
      'SELECT password_hash FROM users WHERE id = $1',
      [user.id]
    );

    if (!userWithHash || !await verifyPassword(password, userWithHash.password_hash)) {
      return NextResponse.json(
        { error: { code: 'AUTH_INVALID_CREDENTIALS', message: 'Invalid email or password' } },
        { status: 401 }
      );
    }

    // Update last login
    await query('UPDATE users SET last_login_at = NOW() WHERE id = $1', [user.id]);

    // Sign JWT
    const tier = user.tier || 'trial';
    const accessToken = signAccessToken({ sub: user.id, email: user.email, tier });

    // For local app: generate and store license token
    let licenseToken = null;
    if (device_name || device_id) {
      const tokenData = signLicenseToken({
        sub: user.id,
        email: user.email,
        tier,
        device_id
      });

      // Store license token hash
      await query(
        `INSERT INTO license_tokens (user_id, token_hash, device_name, device_id, tier, expires_at)
         VALUES ($1, $2, $3, $4, $5, NOW() + INTERVAL '30 days')
         ON CONFLICT (user_id, device_id) DO UPDATE
         SET token_hash = $2, tier = $5, expires_at = NOW() + INTERVAL '30 days', last_seen_at = NOW()`,
        [user.id, crypto.createHash('sha256').update(tokenData.raw).digest('hex'), device_name, device_id, tier]
      );

      licenseToken = tokenData.raw;
    }

    return NextResponse.json({
      access_token: accessToken,
      license_token: licenseToken,
      user: { id: user.id, email: user.email },
      tier
    });

  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Login failed' } },
      { status: 500 }
    );
  }
}
