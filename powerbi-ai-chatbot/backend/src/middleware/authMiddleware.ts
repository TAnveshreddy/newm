import { NextFunction, Request, Response } from 'express';
import { getTokenValidator, TokenValidationError } from '../auth/entraId';
import { UserContext } from '../models/types';

/** Express request augmented with the authenticated user. */
export interface AuthenticatedRequest extends Request {
  user?: UserContext;
}

/**
 * Authentication middleware (Phase 5 / Phase 11). Every protected route must
 * pass a valid Entra ID bearer token. Extracts, validates and attaches the
 * UserContext. Returns 401 with a safe message on failure — the raw token is
 * never logged.
 */
export async function requireAuth(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction,
): Promise<void> {
  const header = req.headers.authorization;
  if (!header || !header.startsWith('Bearer ')) {
    res.status(401).json({ error: 'unauthenticated', message: 'Please sign in to continue.' });
    return;
  }
  const token = header.slice('Bearer '.length).trim();

  // Defense in depth: a Power BI token must never be accepted from a prompt or
  // passed as the user's auth token. We only accept our own API audience token,
  // which the validator enforces via audience checking.
  try {
    req.user = await getTokenValidator().validate(token);
    next();
  } catch (err) {
    if (err instanceof TokenValidationError) {
      res.status(401).json({ error: 'unauthenticated', message: 'Please sign in to continue.' });
      return;
    }
    next(err);
  }
}

/** Authorize a route by required app role (optional helper). */
export function requireRole(role: string) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({ error: 'unauthenticated', message: 'Please sign in to continue.' });
      return;
    }
    if (!req.user.roles.includes(role)) {
      res.status(403).json({ error: 'forbidden', message: 'You do not have access to this resource.' });
      return;
    }
    next();
  };
}
