// website/lib/auth.ts
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import crypto from 'crypto';

const JWT_SECRET = process.env.JWT_SECRET || 'change-me-in-production';
const LICENSE_TOKEN_SECRET = process.env.LICENSE_TOKEN_SECRET || JWT_SECRET;

export interface JWTPayload {
  sub: string; // user_id
  email: string;
  tier?: string;
}

export interface LicenseTokenPayload {
  sub: string; // user_id
  email: string;
  tier: string;
  device_id?: string;
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export function signAccessToken(payload: JWTPayload): string {
  return jwt.sign(payload, JWT_SECRET, { expiresIn: '7d' });
}

export function verifyAccessToken(token: string): JWTPayload | null {
  try {
    return jwt.verify(token, JWT_SECRET) as JWTPayload;
  } catch {
    return null;
  }
}

export function generateLicenseToken(): string {
  return crypto.randomBytes(32).toString('hex');
}

export function hashLicenseToken(token: string): string {
  return crypto.createHash('sha256').update(token).digest('hex');
}

export interface LicenseTokenResult {
  raw: string;
  jwt: string;
}

export function signLicenseToken(payload: LicenseTokenPayload): LicenseTokenResult {
  const token = generateLicenseToken();
  const jwtPayload = { ...payload, token };
  // Store the JWT for verification, client gets the raw token
  return {
    raw: token,
    jwt: jwt.sign(jwtPayload, LICENSE_TOKEN_SECRET, { expiresIn: '30d' })
  };
}

export function verifyLicenseToken(jwtToken: string): LicenseTokenPayload | null {
  try {
    return jwt.verify(jwtToken, LICENSE_TOKEN_SECRET) as LicenseTokenPayload;
  } catch {
    return null;
  }
}
