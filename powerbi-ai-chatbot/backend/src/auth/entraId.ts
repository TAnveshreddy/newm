import { createRemoteJWKSet, jwtVerify, JWTPayload } from 'jose';
import { getConfig } from '../config';
import { UserContext } from '../models/types';

/**
 * Entra ID token validation (Phase 5). Validates issuer, audience, expiry and
 * signature against the tenant's JWKS, then maps claims to a UserContext.
 *
 * Security rules enforced here:
 *  - Signature verified against Entra's published keys (createRemoteJWKSet).
 *  - Issuer and audience must match the configured values.
 *  - Tokens are never logged.
 */

export class TokenValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TokenValidationError';
  }
}

export interface TokenValidator {
  validate(rawToken: string): Promise<UserContext>;
}

/** Production validator backed by the tenant JWKS. */
export class EntraTokenValidator implements TokenValidator {
  private jwks: ReturnType<typeof createRemoteJWKSet> | undefined;

  private getJwks() {
    if (!this.jwks) {
      const cfg = getConfig();
      if (!cfg.entra.jwksUri) throw new TokenValidationError('ENTRA_JWKS_URI is not configured.');
      this.jwks = createRemoteJWKSet(new URL(cfg.entra.jwksUri));
    }
    return this.jwks;
  }

  async validate(rawToken: string): Promise<UserContext> {
    const cfg = getConfig();
    let payload: JWTPayload;
    try {
      const result = await jwtVerify(rawToken, this.getJwks(), {
        issuer: cfg.entra.issuer || undefined,
        audience: cfg.entra.audience || undefined,
      });
      payload = result.payload;
    } catch (err) {
      throw new TokenValidationError(`Token validation failed: ${(err as Error).message}`);
    }
    return claimsToUser(payload);
  }
}

/**
 * Mock validator for local/offline development. Accepts a compact
 * "mock:<json>" token or a bare username and returns a synthetic UserContext.
 * NEVER used when mockMode is false.
 */
export class MockTokenValidator implements TokenValidator {
  async validate(rawToken: string): Promise<UserContext> {
    if (rawToken.startsWith('mock:')) {
      try {
        const obj = JSON.parse(rawToken.slice('mock:'.length));
        return {
          userId: obj.userId ?? obj.username ?? 'dev-user',
          username: obj.username ?? 'dev-user@example.com',
          name: obj.name ?? obj.username ?? 'Dev User',
          tenantId: obj.tenantId ?? 'mock-tenant',
          roles: obj.roles ?? [],
          groups: obj.groups ?? [],
        };
      } catch {
        throw new TokenValidationError('Malformed mock token.');
      }
    }
    // Treat any non-empty bearer as a default dev user.
    if (rawToken.trim()) {
      return {
        userId: 'dev-user',
        username: 'dev-user@example.com',
        name: 'Dev User',
        tenantId: 'mock-tenant',
        roles: [],
        groups: [],
      };
    }
    throw new TokenValidationError('Empty token.');
  }
}

export function claimsToUser(payload: JWTPayload): UserContext {
  const oid = (payload.oid as string) ?? (payload.sub as string);
  if (!oid) throw new TokenValidationError('Token missing subject/oid claim.');
  return {
    userId: oid,
    username:
      (payload.preferred_username as string) ??
      (payload.upn as string) ??
      (payload.email as string) ??
      oid,
    name: payload.name as string | undefined,
    tenantId: (payload.tid as string) ?? '',
    roles: normalizeStringArray(payload.roles),
    groups: normalizeStringArray(payload.groups),
  };
}

function normalizeStringArray(value: unknown): string[] {
  if (Array.isArray(value)) return value.filter((v): v is string => typeof v === 'string');
  if (typeof value === 'string') return [value];
  return [];
}

let validator: TokenValidator | undefined;

export function getTokenValidator(): TokenValidator {
  if (!validator) validator = getConfig().mockMode ? new MockTokenValidator() : new EntraTokenValidator();
  return validator;
}

export function setTokenValidatorForTests(v: TokenValidator | undefined): void {
  validator = v;
}
