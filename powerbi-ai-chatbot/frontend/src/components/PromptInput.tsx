import { FormEvent, useState } from 'react';

/** Natural-language prompt input. Submits on Enter (Shift+Enter for newline). */
export function PromptInput({
  disabled,
  onSubmit,
}: {
  disabled: boolean;
  onSubmit: (prompt: string) => void;
}) {
  const [value, setValue] = useState('');

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue('');
  };

  return (
    <form className="prompt-input" onSubmit={submit}>
      <textarea
        value={value}
        disabled={disabled}
        placeholder="Ask about your data, e.g. “Create a bar chart of total sales by region for 2026”"
        rows={2}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) submit(e);
        }}
        aria-label="Message"
      />
      <button type="submit" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  );
}
