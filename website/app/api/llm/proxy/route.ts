// website/app/api/llm/proxy/route.ts
import { NextRequest } from 'next/server';
import { query, queryOne, LicenseToken, TierLimits, UsageLog } from '@/lib/db';
import { streamLLM, buildCompilePrompt, buildQAPrompt, CompileRequest, QARequest } from '@/lib/llm';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { token, action, payload } = body;

    if (!token || !action || !payload) {
      return new Response(
        JSON.stringify({ error: { code: 'VALIDATION_ERROR', message: 'Missing required fields' } }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify license
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');
    const licenseToken = await queryOne<LicenseToken & { user_id: string }>(
      'SELECT * FROM license_tokens WHERE token_hash = $1',
      [tokenHash]
    );

    if (!licenseToken) {
      return new Response(
        JSON.stringify({ error: { code: 'LICENSE_INVALID', message: 'Invalid license token' } }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get tier limits
    const limits = await queryOne<TierLimits>(
      'SELECT * FROM tier_limits WHERE tier = $1',
      [licenseToken.tier]
    );

    if (!limits) {
      return new Response(
        JSON.stringify({ error: { code: 'INTERNAL_ERROR', message: 'Tier limits not found' } }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Check usage limits
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

    const usageCount = await queryOne<{ count: bigint }>(
      `SELECT COUNT(*) as count FROM usage_logs
       WHERE user_id = $1 AND action = $2 AND timestamp >= $3`,
      [licenseToken.user_id, action, monthStart]
    );

    const count = Number(usageCount?.count || 0);
    const maxAction = action === 'compile' ? limits.max_compiles : limits.max_qa;

    if (maxAction !== -1 && count >= maxAction) {
      return new Response(
        JSON.stringify({
          error: { code: 'LIMIT_EXCEEDED', message: `Monthly ${action} limit exceeded` },
          remaining: 0
        }),
        { status: 429, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Select model
    const model = limits.allowed_models[0] || 'gpt-4o-mini';

    // Build prompt based on action
    let prompt: string;
    if (action === 'compile') {
      const req = payload as CompileRequest['payload'];
      prompt = buildCompilePrompt(req.documents);
    } else if (action === 'qa') {
      const req = payload as QARequest['payload'];
      prompt = buildQAPrompt(req.question, req.context);
    } else {
      return new Response(
        JSON.stringify({ error: { code: 'VALIDATION_ERROR', message: 'Invalid action' } }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Stream LLM response
    const stream = await streamLLM(model, [{ role: 'user', content: prompt }]);

    // Log usage (estimate tokens)
    const estimatedTokens = Math.ceil(prompt.length / 4);
    await query(
      `INSERT INTO usage_logs (user_id, action, tokens_used, model)
       VALUES ($1, $2, $3, $4)`,
      [licenseToken.user_id, action, estimatedTokens, model]
    );

    // Return SSE stream
    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('LLM proxy error:', error);
    return new Response(
      JSON.stringify({ error: { code: 'INTERNAL_ERROR', message: 'LLM request failed' } }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
