// website/app/api/auth/refresh/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { queryOne, User } from '@/lib/db';
import { verifyAccessToken, signAccessToken } from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    const { access_token } = await request.json();

    if (!access_token) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Access token is required' } },
        { status: 400 }
      );
    }

    // Verify existing token
    const payload = verifyAccessToken(access_token);
    if (!payload) {
      return NextResponse.json(
        { error: { code: 'AUTH_INVALID_TOKEN', message: 'Invalid or expired token' } },
        { status: 401 }
      );
    }

    // Get user with current subscription tier
    const user = await queryOne<User & { tier: string }>(
      `SELECT u.*, s.tier FROM users u
       LEFT JOIN subscriptions s ON s.user_id = u.id
       WHERE u.id = $1`,
      [payload.sub]
    );

    if (!user) {
      return NextResponse.json(
        { error: { code: 'AUTH_USER_NOT_FOUND', message: 'User not found' } },
        { status: 404 }
      );
    }

    // Issue new token with updated tier
    const newToken = signAccessToken({
      sub: user.id,
      email: user.email,
      tier: user.tier || 'trial'
    });

    return NextResponse.json({
      access_token: newToken,
      user: { id: user.id, email: user.email },
      tier: user.tier || 'trial'
    });

  } catch (error) {
    console.error('Token refresh error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Token refresh failed' } },
      { status: 500 }
    );
  }
}
