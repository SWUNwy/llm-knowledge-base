// website/app/api/stripe/checkout/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { queryOne } from '@/lib/db';
import { createCheckoutSession } from '@/lib/stripe';

export async function POST(request: NextRequest) {
  try {
    const { price_id, email } = await request.json();

    if (!price_id) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Price ID is required' } },
        { status: 400 }
      );
    }

    // Get or create customer
    const user = email ? await queryOne('SELECT * FROM users WHERE email = $1', [email]) : null;

    const session = await createCheckoutSession({
      customerEmail: email,
      priceId: price_id,
      successUrl: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?session_id={CHECKOUT_SESSION_ID}`,
      cancelUrl: `${process.env.NEXT_PUBLIC_APP_URL}/pricing`,
    });

    return NextResponse.json({ url: session.url });

  } catch (error) {
    console.error('Checkout error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to create checkout session' } },
      { status: 500 }
    );
  }
}
