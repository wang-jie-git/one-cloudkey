/**
 * Waitlist Signup API — POST /api/signup
 *
 * Accepts { email: string } and stores via configured backend:
 * 1. KV (if WAITLIST_KV binding is configured in Cloudflare Pages)
 * 2. Webhook (if SIGNUP_WEBHOOK_URL env var is set)
 * 3. Fallback: logs to Cloudflare Pages dashboard
 *
 * Set up KV binding:
 *   Cloudflare Dashboard > Pages > one-cloudkey > Settings > Functions >
 *   KV namespace bindings > add "WAITLIST_KV"
 *
 * Set up webhook (optional):
 *   Cloudflare Dashboard > Pages > one-cloudkey > Settings > Environment variables >
 *   Add SIGNUP_WEBHOOK_URL
 */

export async function onRequest(context) {
  const { request, env } = context;

  // Unified CORS headers
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  // Handle preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  // Only accept POST
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  }

  try {
    const body = await request.json();
    const email = (body.email || '').trim().toLowerCase();

    // Validate email format
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return new Response(JSON.stringify({ error: '请输入有效的邮箱地址 / Please enter a valid email address' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      });
    }

    const timestamp = new Date().toISOString();
    const entry = JSON.stringify({ email, timestamp, source: 'one-cloudkey', ip: request.headers.get('CF-Connecting-IP') || '' });

    // Backend 1: KV storage
    if (env && env.WAITLIST_KV) {
      const key = `signup:${timestamp}`;
      await env.WAITLIST_KV.put(key, entry);
      console.log(`[SIGNUP:KV] ${email} stored as ${key}`);
    }

    // Backend 2: Webhook forwarding (Slack, Discord, Make, etc.)
    if (env && env.SIGNUP_WEBHOOK_URL) {
      await fetch(env.SIGNUP_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, timestamp, source: 'one-cloudkey' }),
      }).catch(e => console.error('[SIGNUP:WEBHOOK] Failed:', e.message));
    }

    // Always log to Cloudflare dashboard
    console.log(`[SIGNUP] ${email} at ${timestamp}`);

    return new Response(JSON.stringify({ success: true, message: '申请提交成功！内测邀请将在48小时内发送至您的邮箱。' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  } catch (err) {
    console.error('[SIGNUP:ERROR]', err.message);
    return new Response(JSON.stringify({ error: '服务器内部错误，请稍后重试。' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  }
}
