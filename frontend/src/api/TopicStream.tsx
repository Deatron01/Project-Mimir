import { createContext, useContext, useEffect, useState } from 'react';
import { useQueryClient, type InfiniteData } from '@tanstack/react-query';
import { subscribeTopicEvents } from './events';
import { qk } from './keys';
import type { Job, MessageList, TopicFile } from './types';

type StreamState = 'connecting' | 'open' | 'retrying' | 'closed';
const StreamCtx = createContext<StreamState>('closed');

/** Current state of the topic event stream (used to decide whether to poll). */
export const useTopicStreamState = (): StreamState => useContext(StreamCtx);

/**
 * Opens the SSE stream for a topic while the workspace is mounted and folds every event into the
 * TanStack Query cache, so all panes update without their own subscriptions.
 */
export function TopicStreamProvider({
  topicId,
  onTopicDeleted,
  children,
}: {
  topicId: string;
  onTopicDeleted?: () => void;
  children: React.ReactNode;
}) {
  const qc = useQueryClient();
  const [state, setState] = useState<StreamState>('connecting');

  useEffect(() => {
    const upsertJob = (job: Job) => {
      qc.setQueryData(qk.job(job.id), job);
      qc.setQueryData<Job[]>(qk.activeJobs, (prev) => {
        if (!prev) return prev;
        const done = job.status === 'succeeded' || job.status === 'failed' || job.status === 'cancelled';
        const rest = prev.filter((j) => j.id !== job.id);
        return done ? rest : [...rest, job];
      });
    };

    return subscribeTopicEvents(topicId, {
      onStateChange: setState,
      onEvent: (name, data) => {
        switch (name) {
          case 'file.status': {
            const file = data.file as TopicFile | undefined;
            if (!file) break;
            qc.setQueryData<TopicFile[]>(qk.files(topicId), (prev) =>
              prev ? (prev.some((f) => f.id === file.id) ? prev.map((f) => (f.id === file.id ? file : f)) : [file, ...prev]) : prev,
            );
            if (file.status === 'ready' || file.status === 'failed') void qc.invalidateQueries({ queryKey: qk.topic(topicId) });
            break;
          }
          case 'job.progress':
            if (data.job) upsertJob(data.job);
            break;
          case 'job.succeeded':
          case 'job.failed': {
            if (!data.job) break;
            upsertJob(data.job);
            const r = data.job.result;
            if (data.job.type === 'generate_test' || data.job.type === 'answer_question') {
              void qc.invalidateQueries({ queryKey: qk.topicTestsAll(topicId) });
              void qc.invalidateQueries({ queryKey: qk.sessions(topicId) });
            }
            if (data.job.type === 'regenerate_question' && r?.test_id) {
              void qc.invalidateQueries({ queryKey: qk.test(topicId, r.test_id) });
            }
            void qc.invalidateQueries({ queryKey: qk.topic(topicId) });
            break;
          }
          case 'message.created': {
            const m = data.message;
            if (!m) break;
            qc.setQueryData<InfiniteData<MessageList, string | undefined>>(qk.messages(topicId, m.session_id), (prev) => {
              if (!prev) return prev;
              const [first, ...rest] = prev.pages;
              if (prev.pages.some((p) => p.items.some((x) => x.id === m.id))) return prev;
              return { ...prev, pages: [{ ...first, items: [m, ...first.items] }, ...rest] };
            });
            void qc.invalidateQueries({ queryKey: qk.sessions(topicId) });
            break;
          }
          case 'topic.deleted':
            qc.removeQueries({ queryKey: qk.topic(topicId) });
            void qc.invalidateQueries({ queryKey: qk.topicsAll });
            onTopicDeleted?.();
            break;
          default:
            break;
        }
      },
    });
    // onTopicDeleted is intentionally not a dependency: a new callback must not reopen the stream.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topicId, qc]);

  return <StreamCtx.Provider value={state}>{children}</StreamCtx.Provider>;
}
