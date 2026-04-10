// website/app/api/license/verify/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne, LicenseToken, TierLimits } from '@/lib/db';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const { token } = await request.json();

    if (!token) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'License token is required' } },
        { status: 400 }
      );
    }

    // Look up license token by hash
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');
    const licenseToken = await queryOne<LicenseToken & { email: string; subscription_status: string }>(
      `SELECT lt.*, u.email, s.status as subscription_status
       FROM license_tokens lt
       JOIN users u ON u.id = lt.user_id
       LEFT JOIN subscriptions s ON s.user_id = u.id
       WHERE lt.token_hash = $1`,
      [tokenHash]
    );

    if (!licenseToken) {
      return NextResponse.json(
        { error: { code: 'LICENSE_INVALID', message: 'Invalid license token' } },
        { status: 401 }
      );
    }

    // Check if expired
    if (licenseToken.expires_at && new Date() > licenseToken.expires_at) {
      return NextResponse.json(
        { error: { code: 'LICENSE_EXPIRED', message: 'License token has expired' } },
        { status: 401 }
      );
    }

    // Check if subscription is active
    const subStatus = licenseToken.subscription_status;
    if (subStatus && subStatus !== 'active' && subStatus !== 'trialing') {
      return NextResponse.json(
        { error: { code: 'LICENSE_SUSPENDED', message: 'Subscription is not active' } },
        { status: 403 }
      );
    }

    // Get tier limits
    const limits = await queryOne<TierLimits>(
      'SELECT * FROM tier_limits WHERE tier = $1',
      [licenseToken.tier]
    );

    // Update last seen
    await query('UPDATE license_tokens SET last_seen_at = NOW() WHERE id = $1', [licenseToken.id]);

    return NextResponse.json({
      valid: true,
      user: {
        id: licenseToken.user_id,
        email: licenseToken.email
      },
      tier: licenseToken.tier,
      limits: limits || {
        max_compiles: -1,
        max_qa: -1,
        allowed_models: [],
        max_documents: null
      }
    });

  } catch (error) {
    console.error('License verify error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'License verification failed' } },
      { status: 500 }
    );
  }
}
