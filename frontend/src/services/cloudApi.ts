// frontend/src/services/cloudApi.ts
const CLOUD_API_URL = process.env.CLOUD_API_URL || 'https://knowledgebase.ai';

export interface LoginResponse {
  access_token: string;
  license_token?: string;
  tier?: string;
  user?: { id: string; email: string };
}

export interface LicenseVerifyResponse {
  valid: boolean;
  user?: { id: string; email: string };
  tier?: string;
  limits?: {
    max_compiles: number;
    max_qa: number;
    allowed_models: string[];
  };
}

export interface UsageResponse {
  period: { start: string; end: string };
  usage: { compile: number; qa: number };
}

export async function cloudLogin(
  email: string,
  password: string,
  deviceId?: string
): Promise<LoginResponse> {
  const response = await fetch(`${CLOUD_API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      password,
      device_id: deviceId || 'web-client'
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Login failed');
  }

  return response.json();
}

export async function verifyLicense(token: string): Promise<LicenseVerifyResponse> {
  const response = await fetch(`${CLOUD_API_URL}/api/license/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  });

  if (!response.ok) {
    throw new Error('License verification failed');
  }

  return response.json();
}

export async function getUsage(token: string): Promise<UsageResponse> {
  const response = await fetch(`${CLOUD_API_URL}/api/usage/current`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  });

  if (!response.ok) {
    throw new Error('Failed to fetch usage');
  }

  return response.json();
}
