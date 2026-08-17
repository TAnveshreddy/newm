import { useEffect, useMemo, useState } from 'react';
import { ApiClient, ApiError } from '../services/api';
import { useAuth } from '../auth/useAuth';
import { ChatMessage, ModelSummary } from '../models/types';
import { MessageList } from './MessageList';
import { PromptInput } from './PromptInput';
import { LoadingState } from './LoadingState';
import { ErrorState } from './ErrorState';

let messageSeq = 0;
const nextId = () => `m${messageSeq++}`;

/**
 * Main chat surface. Owns conversation state (conversationId + transcript),
 * loads the authorized models, and drives the /api/chat request cycle.
 */
export function ChatWindow() {
  const { getToken, username, logout } = useAuth();
  const api = useMemo(() => new ApiClient(getToken), [getToken]);

  const [models, setModels] = useState<ModelSummary[]>([]);
  const [modelId, setModelId] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    let cancelled = false;
    api
      .listModels()
      .then(({ models }) => {
        if (cancelled) return;
        setModels(models);
        if (models[0]) setModelId(models[0].modelId);
      })
      .catch((e: unknown) => setError(errText(e)));
    return () => {
      cancelled = true;
    };
  }, [api]);

  const send = async (prompt: string) => {
    setError(undefined);
    setMessages((prev) => [...prev, { id: nextId(), role: 'user', text: prompt }]);
    setLoading(true);
    try {
      const res = await api.chat(modelId, prompt, conversationId);
      setConversationId(res.conversationId);
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: 'assistant',
          text: res.message,
          visual: res.visual,
          result: res.result,
          status: res.status,
        },
      ]);
    } catch (e: unknown) {
      setError(errText(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-window">
      <header className="chat-header">
        <div className="chat-title">Power BI AI Chatbot</div>
        <div className="chat-controls">
          <label className="model-select">
            Model
            <select value={modelId} onChange={(e) => setModelId(e.target.value)} disabled={loading}>
              {models.map((m) => (
                <option key={m.modelId} value={m.modelId}>
                  {m.displayName}
                </option>
              ))}
            </select>
          </label>
          <span className="user-chip" title={username}>
            {username}
          </span>
          <button className="logout-btn" onClick={() => void logout()}>
            Sign out
          </button>
        </div>
      </header>

      {messages.length === 0 && (
        <div className="empty-state">
          <p>Ask a question about your authorized semantic model.</p>
          <ul>
            <li>“What are total sales for 2026?”</li>
            <li>“Create a bar chart of sales by region for 2026.”</li>
            <li>“Change it to a line chart.”</li>
            <li>“Only show APAC.”</li>
          </ul>
        </div>
      )}

      <MessageList messages={messages} />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onDismiss={() => setError(undefined)} />}

      <PromptInput disabled={loading || !modelId} onSubmit={send} />
    </div>
  );
}

function errText(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  if (e instanceof Error) return e.message;
  return 'Something went wrong. Please try again.';
}
