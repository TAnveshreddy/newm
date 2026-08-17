import { Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authMiddleware';
import { conversationStore } from '../services/conversation/conversationStore';

/**
 * GET /api/conversations/:id — retrieves conversation context if persistence is
 * enabled. Ownership is enforced by the store (a user can only read their own
 * conversations). Returns only the minimum necessary state.
 */
export function getConversationController(req: AuthenticatedRequest, res: Response): void {
  const state = conversationStore.get(req.user!.userId, req.params.id);
  if (!state) {
    res.status(404).json({ error: 'not_found', message: 'Conversation not found.' });
    return;
  }
  res.json({
    conversationId: state.conversationId,
    modelId: state.modelId,
    lastFilters: state.lastFilters,
    lastVisual: state.lastVisual,
    updatedAt: state.updatedAt,
  });
}
