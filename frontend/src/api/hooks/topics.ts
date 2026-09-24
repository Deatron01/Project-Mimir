import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import { unwrap } from '../errors';
import { qk } from '../keys';
import type { Topic, TopicInput, TopicPatch } from '../types';

export function useTopics(q = '') {
  return useQuery({
    queryKey: qk.topics(q),
    queryFn: async () => unwrap(await api().GET('/topics', { params: { query: { q: q || undefined, limit: 100 } } })),
    placeholderData: (prev) => prev,
    // A topic being deleted disappears when its cascade job finishes; poll until then.
    refetchInterval: (q) => (q.state.data?.items.some((t) => t.status === 'deleting') ? 2000 : false),
  });
}

export function useTopic(topicId: string | undefined) {
  return useQuery({
    queryKey: qk.topic(topicId ?? ''),
    enabled: Boolean(topicId),
    queryFn: async () => unwrap(await api().GET('/topics/{topicId}', { params: { path: { topicId: topicId! } } })),
  });
}

export function useCreateTopic() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: TopicInput) => unwrap(await api().POST('/topics', { body: input })),
    onSuccess: (topic) => {
      qc.setQueryData(qk.topic(topic.id), topic);
      void qc.invalidateQueries({ queryKey: qk.topicsAll });
      void qc.invalidateQueries({ queryKey: qk.me });
    },
  });
}

export function useUpdateTopic(topicId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (patch: TopicPatch) =>
      unwrap(await api().PATCH('/topics/{topicId}', { params: { path: { topicId } }, body: patch })),
    onMutate: async (patch) => {
      await qc.cancelQueries({ queryKey: qk.topic(topicId) });
      const prev = qc.getQueryData<Topic>(qk.topic(topicId));
      if (prev) qc.setQueryData<Topic>(qk.topic(topicId), { ...prev, ...patch });
      return { prev };
    },
    onError: (_e, _p, ctx) => ctx?.prev && qc.setQueryData(qk.topic(topicId), ctx.prev),
    onSuccess: (topic) => qc.setQueryData(qk.topic(topicId), topic),
    onSettled: () => qc.invalidateQueries({ queryKey: qk.topicsAll }),
  });
}

export function useDeleteTopic() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (topicId: string) =>
      unwrap(await api().DELETE('/topics/{topicId}', { params: { path: { topicId } } })),
    onSuccess: (_r, topicId) => {
      qc.removeQueries({ queryKey: qk.topic(topicId) });
      void qc.invalidateQueries({ queryKey: qk.topicsAll });
      void qc.invalidateQueries({ queryKey: qk.savedTests });
      void qc.invalidateQueries({ queryKey: qk.me });
    },
  });
}
