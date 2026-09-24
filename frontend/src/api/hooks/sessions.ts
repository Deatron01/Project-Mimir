import { useInfiniteQuery, useMutation, useQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query';
import { api } from '../client';
import { unwrap } from '../errors';
import { qk } from '../keys';
import type { ChatSession, MessageInput, MessageList } from '../types';

export function useSessions(topicId: string) {
  return useQuery({
    queryKey: qk.sessions(topicId),
    queryFn: async () =>
      unwrap(await api().GET('/topics/{topicId}/sessions', { params: { path: { topicId } } })).items,
  });
}

export function useCreateSession(topicId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (title?: string) =>
      unwrap(await api().POST('/topics/{topicId}/sessions', { params: { path: { topicId } }, body: title ? { title } : {} })),
    onSuccess: (s) => qc.setQueryData<ChatSession[]>(qk.sessions(topicId), (prev = []) => [s, ...prev]),
  });
}

export function useRenameSession(topicId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ sessionId, title }: { sessionId: string; title: string }) =>
      unwrap(
        await api().PATCH('/topics/{topicId}/sessions/{sessionId}', { params: { path: { topicId, sessionId } }, body: { title } }),
      ),
    onSuccess: (s) => qc.setQueryData<ChatSession[]>(qk.sessions(topicId), (prev) => prev?.map((x) => (x.id === s.id ? s : x))),
  });
}

export function useDeleteSession(topicId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: string) =>
      unwrap(await api().DELETE('/topics/{topicId}/sessions/{sessionId}', { params: { path: { topicId, sessionId } } })),
    onSuccess: (_r, sessionId) => {
      qc.setQueryData<ChatSession[]>(qk.sessions(topicId), (prev) => prev?.filter((x) => x.id !== sessionId));
      qc.removeQueries({ queryKey: qk.messages(topicId, sessionId) });
      void qc.invalidateQueries({ queryKey: qk.topicTestsAll(topicId) });
    },
  });
}

/** Messages come newest first from the API; pages are loaded backwards in time. */
export function useMessages(topicId: string, sessionId: string | undefined) {
  return useInfiniteQuery({
    queryKey: qk.messages(topicId, sessionId ?? ''),
    enabled: Boolean(sessionId),
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam }) =>
      unwrap(
        await api().GET('/topics/{topicId}/sessions/{sessionId}/messages', {
          params: { path: { topicId, sessionId: sessionId! }, query: { cursor: pageParam, limit: 50 } },
        }),
      ),
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  });
}

export async function postMessageTo(topicId: string, sessionId: string, body: MessageInput) {
  return unwrap(
    await api().POST('/topics/{topicId}/sessions/{sessionId}/messages', { params: { path: { topicId, sessionId } }, body }),
  );
}

export function usePostMessage(topicId: string, sessionId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: MessageInput) => postMessageTo(topicId, sessionId, body),
    onSuccess: ({ message }) => {
      qc.setQueryData<InfiniteData<MessageList, string | undefined>>(qk.messages(topicId, sessionId), (prev) => {
        if (!prev) return prev;
        const [first, ...rest] = prev.pages;
        return { ...prev, pages: [{ ...first, items: [message, ...first.items.filter((m) => m.id !== message.id)] }, ...rest] };
      });
      void qc.invalidateQueries({ queryKey: qk.activeJobs });
      void qc.invalidateQueries({ queryKey: qk.sessions(topicId) });
    },
  });
}
