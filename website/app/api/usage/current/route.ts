// website/app/api/usage/current/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne, LicenseToken } from '@/lib/db';
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

    // Verify license
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');
    const licenseToken = await queryOne<LicenseToken>(
      'SELECT user_id FROM license_tokens WHERE token_hash = $1',
      [tokenHash]
    );

    if (!licenseToken) {
      return NextResponse.json(
        { error: { code: 'LICENSE_INVALID', message: 'Invalid license token' } },
        { status: 401 }
      );
    }

    // Get current month usage
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

    const compileCount = await queryOne<{ count: bigint }>(
      `SELECT COUNT(*) as count FROM usage_logs
       WHERE user_id = $1 AND action = 'compile' AND timestamp >= $2`,
      [licenseToken.user_id, monthStart]
    );

    const qaCount = await queryOne<{ count: bigint }>(
      `SELECT COUNT(*) as count FROM usage_logs
       WHERE user_id = $1 AND action = 'qa' AND timestamp >= $2`,
      [licenseToken.user_id, monthStart]
    );

    return NextResponse.json({
      period: {
        start: monthStart.toISOString(),
        end: new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString()
      },
      usage: {
        compile: Number(compileCount?.count || 0),
        qa: Number(qaCount?.count || 0)
      }
    });

  } catch (error) {
    console.error('Usage query error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch usage' } },
      { status: 500 }
    );
  }
}
