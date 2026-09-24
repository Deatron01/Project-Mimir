import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import { unwrap } from '../errors';
import { qk } from '../keys';
import type { Job } from '../types';
import { useAuth } from '../../context/AuthContext';

export const isJobDone = (j?: Pick<Job, 'status'> | null) =>
  !!j && (j.status === 'succeeded' || j.status === 'failed' || j.status === 'cancelled');

export function useActiveJobs() {
  const { user } = useAuth();
  return useQuery({
    queryKey: qk.activeJobs,
    enabled: Boolean(user),
    queryFn: async () => unwrap(await api().GET('/jobs', { params: { query: { active: true } } })).items,
    refetchInterval: (q) => ((q.state.data?.length ?? 0) > 0 ? 4000 : 30_000),
  });
}

/** Follows one job. SSE pushes updates into this cache entry; polling is the fallback. */
export function useJob(jobId: string | null | undefined, pollMs = 2000) {
  return useQuery({
    queryKey: qk.job(jobId ?? ''),
    enabled: Boolean(jobId),
    queryFn: async () => unwrap(await api().GET('/jobs/{jobId}', { params: { path: { jobId: jobId! } } })),
    refetchInterval: (q) => (isJobDone(q.state.data) ? false : pollMs),
  });
}

export function useCancelJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => unwrap(await api().POST('/jobs/{jobId}/cancel', { params: { path: { jobId } } })),
    onSuccess: (job) => {
      qc.setQueryData(qk.job(job.id), job);
      void qc.invalidateQueries({ queryKey: qk.activeJobs });
    },
  });
}
