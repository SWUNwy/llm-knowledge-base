// website/app/api/license/status/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { queryOne, LicenseToken } from '@/lib/db';
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
    const licenseToken = await queryOne<LicenseToken & { email: string }>(
      `SELECT lt.*, u.email
       FROM license_tokens lt
       JOIN users u ON u.id = lt.user_id
       WHERE lt.token_hash = $1`,
      [tokenHash]
    );

    if (!licenseToken) {
      return NextResponse.json(
        {
          valid: false,
          error: 'Invalid license token'
        },
        { status: 401 }
      );
    }

    // Check if expired
    const isExpired = licenseToken.expires_at && new Date() > licenseToken.expires_at;

    return NextResponse.json({
      valid: !isExpired,
      user: {
        id: licenseToken.user_id,
        email: licenseToken.email
      },
      tier: licenseToken.tier,
      device_name: licenseToken.device_name,
      expires_at: licenseToken.expires_at,
      last_seen_at: licenseToken.last_seen_at,
      created_at: licenseToken.created_at
    });

  } catch (error) {
    console.error('License status error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch license status' } },
      { status: 500 }
    );
  }
}
