import { Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authMiddleware';

/** GET /api/me — returns the authenticated user's identity/claims. */
export function meController(req: AuthenticatedRequest, res: Response): void {
  const user = req.user!;
  res.json({
    userId: user.userId,
    username: user.username,
    name: user.name,
    tenantId: user.tenantId,
    roles: user.roles,
    groups: user.groups,
  });
}
