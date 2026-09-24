import { fetchEventSource, EventStreamContentType } from '@microsoft/fetch-event-source';
import { apiUrl, applySession, refreshSession } from './client';
import { getAccessToken } from './tokens';
import type { TopicEvent, TopicEventName } from './types';

class FatalStreamError extends Error {}

export interface TopicStreamHandlers {
  onEvent: (name: TopicEventName, data: TopicEvent) => void;
  onStateChange?: (state: 'connecting' | 'open' | 'retrying' | 'closed') => void;
}

/**
 * Subscribes to `GET /topics/{id}/events`. Uses fetch (not EventSource) so the bearer token can be sent;
 * reconnects with backoff and resumes via Last-Event-ID. Returns an unsubscribe function.
 */
export function subscribeTopicEvents(topicId: string, h: TopicStreamHandlers): () => void {
  const ctrl = new AbortController();
  let attempt = 0;
  h.onStateChange?.('connecting');

  void fetchEventSource(apiUrl(`/topics/${encodeURIComponent(topicId)}/events`), {
    signal: ctrl.signal,
    credentials: 'include',
    openWhenHidden: false,
    // Re-read the token on every (re)connect – it may have been refreshed.
    fetch: (input, init) => {
      const headers = new Headers(init?.headers);
      const token = getAccessToken();
      if (token) headers.set('Authorization', `Bearer ${token}`);
      return fetch(input, { ...init, headers });
    },
    async onopen(res) {
      if (res.ok && res.headers.get('content-type')?.includes(EventStreamContentType)) {
        attempt = 0;
        h.onStateChange?.('open');
        return;
      }
      if (res.status === 401) {
        const session = await refreshSession();
        if (session) {
          applySession(session);
          throw new Error('retry with new token');
        }
        applySession(null, 'expired');
      }
      if (res.status >= 400 && res.status < 500 && res.status !== 429) throw new FatalStreamError(String(res.status));
      throw new Error(`stream ${res.status}`);
    },
    onmessage(ev) {
      if (!ev.event || ev.event === 'heartbeat') return;
      let data: TopicEvent = {};
      try {
        data = ev.data ? (JSON.parse(ev.data) as TopicEvent) : {};
      } catch {
        return;
      }
      h.onEvent(ev.event as TopicEventName, data);
    },
    onclose() {
      // Server closed the stream: let the library reconnect.
      throw new Error('closed');
    },
    onerror(err) {
      if (err instanceof FatalStreamError) {
        h.onStateChange?.('closed');
        throw err; // stop retrying
      }
      h.onStateChange?.('retrying');
      attempt += 1;
      return Math.min(30_000, 1000 * 2 ** Math.min(attempt, 5));
    },
  }).catch(() => h.onStateChange?.('closed'));

  return () => {
    ctrl.abort();
    h.onStateChange?.('closed');
  };
}
