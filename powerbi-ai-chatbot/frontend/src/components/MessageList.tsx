import { useEffect, useRef } from 'react';
import { ChatMessage } from '../models/types';
import { Visualization } from './Visualization';

/** Renders the conversation transcript, including inline visuals. */
export function MessageList({ messages }: { messages: ChatMessage[] }) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="message-list">
      {messages.map((m) => (
        <div key={m.id} className={`message message-${m.role}`}>
          <div className="message-bubble">
            <div className="message-text">{m.text}</div>
            {m.visual && m.result && (
              <div className="message-visual">
                <Visualization spec={m.visual} result={m.result} />
              </div>
            )}
          </div>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
