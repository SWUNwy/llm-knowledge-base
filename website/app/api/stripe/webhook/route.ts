// website/app/api/stripe/webhook/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne } from '@/lib/db';
import { constructWebhookEvent } from '@/lib/stripe';

export async function POST(request: NextRequest) {
  try {
    const payload = await request.text();
    const signature = request.headers.get('stripe-signature')!;

    const event = await constructWebhookEvent(payload, signature);

    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as any;
        const customerId = session.customer;
        const subscriptionId = session.subscription;

        // Get price to determine tier
        const subscription = await fetch(`https://api.stripe.com/v1/subscriptions/${subscriptionId}`, {
          headers: { Authorization: `Bearer ${process.env.STRIPE_SECRET_KEY!}` }
        }).then(r => r.json());

        const priceId = subscription.items.data[0].price.id;
        let tier = 'personal';
        if (priceId.includes('professional')) tier = 'professional';
        if (priceId.includes('team')) tier = 'team';

        // Find user by customer email or create new
        const customerEmail = session.customer_details?.email;
        if (customerEmail) {
          let user = await queryOne('SELECT * FROM users WHERE email = $1', [customerEmail]);
          if (!user) {
            user = await queryOne(
              `INSERT INTO users (email, password_hash) VALUES ($1, 'oauth-login')
               RETURNING *`,
              [customerEmail]
            );
          }

          // Create or update subscription
          await query(
            `INSERT INTO subscriptions (user_id, stripe_customer_id, stripe_subscription_id, stripe_price_id, status, tier, current_period_start, current_period_end)
             VALUES ($1, $2, $3, $4, 'active', $5, NOW(), NOW() + INTERVAL '1 month')
             ON CONFLICT (user_id) DO UPDATE SET
               stripe_customer_id = $2,
               stripe_subscription_id = $3,
               stripe_price_id = $4,
               status = 'active',
               tier = $5,
               current_period_end = NOW() + INTERVAL '1 month'`,
            [user.id, customerId, subscriptionId, priceId, tier]
          );
        }
        break;
      }

      case 'customer.subscription.updated': {
        const subscription = event.data.object as any;
        const subscriptionId = subscription.id;
        const status = subscription.status;
        const priceId = subscription.items.data[0].price.id;

        let tier = 'personal';
        if (priceId.includes('professional')) tier = 'professional';
        if (priceId.includes('team')) tier = 'team';
        if (status === 'canceled') tier = 'free';

        await query(
          `UPDATE subscriptions
             SET status = $1, tier = $2, updated_at = NOW()
             WHERE stripe_subscription_id = $3`,
          [status, tier, subscriptionId]
        );
        break;
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as any;
        await query(
          `UPDATE subscriptions
             SET status = 'canceled', tier = 'free', updated_at = NOW()
             WHERE stripe_subscription_id = $1`,
          [subscription.id]
        );
        break;
      }

      case 'invoice.payment_succeeded': {
        const invoice = event.data.object as any;
        const subscriptionId = invoice.subscription;
        await query(
          `UPDATE subscriptions
             SET current_period_end = NOW() + INTERVAL '1 month', updated_at = NOW()
             WHERE stripe_subscription_id = $1`,
          [subscriptionId]
        );
        break;
      }

      case 'invoice.payment_failed': {
        const invoice = event.data.object as any;
        await query(
          `UPDATE subscriptions
             SET status = 'past_due', updated_at = NOW()
             WHERE stripe_subscription_id = $1`,
          [invoice.subscription]
        );
        break;
      }
    }

    return NextResponse.json({ received: true });

  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Webhook processing failed' } },
      { status: 500 }
    );
  }
}
