import { NextFunction, Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authMiddleware';
import { aiOrchestrator } from '../services/ai/aiOrchestrator';

interface ChatBody {
  modelId?: string;
  prompt?: string;
  conversationId?: string;
}

/**
 * POST /api/chat — main natural-language request endpoint. Delegates to the
 * controlled AI orchestration pipeline and returns a typed ChatResponse.
 *
 * Input validation (Phase 11): prompt and modelId are required and length-
 * bounded; the raw prompt is never concatenated into any query.
 */
export async function chatController(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction,
): Promise<void> {
  try {
    const body = (req.body ?? {}) as ChatBody;
    const prompt = typeof body.prompt === 'string' ? body.prompt.trim() : '';
    const modelId = typeof body.modelId === 'string' ? body.modelId.trim() : '';

    if (!prompt) {
      res.status(400).json({ error: 'invalid_request', message: 'A prompt is required.' });
      return;
    }
    if (prompt.length > 2000) {
      res.status(400).json({ error: 'invalid_request', message: 'The prompt is too long.' });
      return;
    }
    if (!modelId) {
      res.status(400).json({ error: 'invalid_request', message: 'A modelId is required.' });
      return;
    }

    const response = await aiOrchestrator.handleChat({
      user: req.user!,
      modelId,
      prompt,
      conversationId: body.conversationId,
    });
    res.json(response);
  } catch (err) {
    next(err);
  }
}
