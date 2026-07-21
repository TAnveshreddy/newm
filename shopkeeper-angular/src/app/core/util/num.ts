/** Coerce anything to a finite number (0 on failure). */
export function num(v: unknown): number {
  const n = typeof v === 'number' ? v : parseFloat(String(v ?? ''));
  return Number.isFinite(n) ? n : 0;
}

/** Round to 2 decimals, avoiding binary float drift. */
export function round2(v: number): number {
  return Math.round((num(v) + Number.EPSILON) * 100) / 100;
}

/** Today as an ISO yyyy-mm-dd string (local time). */
export function todayISO(d = new Date()): string {
  return (
    d.getFullYear() +
    '-' +
    String(d.getMonth() + 1).padStart(2, '0') +
    '-' +
    String(d.getDate()).padStart(2, '0')
  );
}

/** Shift an ISO date by a number of days. */
export function addDays(iso: string, days: number): string {
  const d = new Date(iso + 'T00:00:00');
  d.setDate(d.getDate() + days);
  return todayISO(d);
}

/** Generate a short, collision-resistant id (matches the original scheme). */
export function makeId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}
