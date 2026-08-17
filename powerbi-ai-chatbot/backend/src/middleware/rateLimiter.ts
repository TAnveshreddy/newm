import { NextFunction, Response } from 'express';
import { getConfig } from '../config';
import { AuthenticatedRequest } from './authMiddleware';

/**
 * Per-user sliding-window rate limiter for chat/query endpoints (Phase 11).
 * In-memory and process-local; for multi-instance production, back it with a
 * shared store (e.g. Redis) or use a platform gateway policy.
 */
export class RateLimiter {
  private readonly hits = new Map<string, number[]>();

  constructor(
    private readonly limit = getConfig().limits.chatRateLimitPerMinute,
    private readonly windowMs = 60_000,
  ) {}

  /** Returns true if the request is allowed, false if the limit is exceeded. */
  check(key: string, now = Date.now()): boolean {
    const windowStart = now - this.windowMs;
    const timestamps = (this.hits.get(key) ?? []).filter((t) => t > windowStart);
    if (timestamps.length >= this.limit) {
      this.hits.set(key, timestamps);
      return false;
    }
    timestamps.push(now);
    this.hits.set(key, timestamps);
    return true;
  }
}

const limiter = new RateLimiter();

export function rateLimit(req: AuthenticatedRequest, res: Response, next: NextFunction): void {
  const key = req.user?.userId ?? req.ip ?? 'anonymous';
  if (!limiter.check(key)) {
    res.status(429).json({ error: 'rate_limited', message: 'Too many requests. Please slow down.' });
    return;
  }
  next();
}

export { limiter as sharedRateLimiter };
