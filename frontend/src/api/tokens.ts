/**
 * Access token held in memory only (never in localStorage) – FE-04 / TOP security requirement.
 * The refresh token lives in an HttpOnly cookie the page cannot read.
 */
type Listener = (token: string | null) => void;

let accessToken: string | null = null;
const listeners = new Set<Listener>();

export const getAccessToken = (): string | null => accessToken;
export function setAccessToken(token: string | null): void {
  accessToken = token;
  listeners.forEach((l) => l(token));
}
export function onAccessTokenChange(l: Listener): () => void {
  listeners.add(l);
  return () => listeners.delete(l);
}
