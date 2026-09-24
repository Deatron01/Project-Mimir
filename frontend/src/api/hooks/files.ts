import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import { unwrap } from '../errors';
import { qk } from '../keys';
import { uploadFiles } from '../upload';
import type { TopicFile } from '../types';
import { useTopicStreamState } from '../TopicStream';

export const isFileSettled = (f: TopicFile) => f.status === 'ready' || f.status === 'failed';

export function useFiles(topicId: string) {
  const stream = useTopicStreamState();
  return useQuery({
    queryKey: qk.files(topicId),
    queryFn: async () =>
      unwrap(await api().GET('/topics/{topicId}/files', { params: { path: { topicId } } })).items,
    // Live updates come over SSE; poll only while something is processing and the stream is down.
    refetchInterval: (q) => (stream !== 'open' && q.state.data?.some((f) => !isFileSettled(f)) ? 3000 : false),
  });
}

export function useUploadFiles(topicId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ files, onProgress, signal }: { files: File[]; onProgress?: (f: number) => void; signal?: AbortSignal }) =>
      uploadFiles(topicId, files, { onProgress, signal }),
    onSuccess: (res) => {
      qc.setQueryData<TopicFile[]>(qk.files(topicId), (prev = []) => [
        ...res.files,
        ...prev.filter((f) => !res.files.some((n) => n.id === f.id)),
      ]);
      void qc.invalidateQueries({ queryKey: qk.topic(topicId) });
      void qc.invalidateQueries({ queryKey: qk.activeJobs });
    },
  });
}

export function useRetryFile(topicId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (fileId: string) =>
      unwrap(await api().POST('/topics/{topicId}/files/{fileId}/retry', { params: { path: { topicId, fileId } } })),
    onSuccess: (_r, fileId) => {
      qc.setQueryData<TopicFile[]>(qk.files(topicId), (prev) =>
        prev?.map((f) => (f.id === fileId ? { ...f, status: 'queued', error_code: null } : f)),
      );
      void qc.invalidateQueries({ queryKey: qk.activeJobs });
    },
  });
}

export function useDeleteFile(topicId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (fileId: string) =>
      unwrap(await api().DELETE('/topics/{topicId}/files/{fileId}', { params: { path: { topicId, fileId } } })),
    onSuccess: (_r, fileId) => {
      qc.setQueryData<TopicFile[]>(qk.files(topicId), (prev) => prev?.filter((f) => f.id !== fileId));
      void qc.invalidateQueries({ queryKey: qk.topic(topicId) });
    },
  });
}
