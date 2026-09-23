import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import { unwrap } from '../errors';
import { qk } from '../keys';
import type { Exam, ExportRequest, Test } from '../types';

export function useTopicTests(topicId: string, saved?: boolean) {
  return useQuery({
    queryKey: qk.topicTests(topicId, saved),
    queryFn: async () =>
      unwrap(await api().GET('/topics/{topicId}/tests', { params: { path: { topicId }, query: { saved } } })).items,
  });
}

export function useTest(topicId: string, testId: string | undefined) {
  return useQuery({
    queryKey: qk.test(topicId, testId ?? ''),
    enabled: Boolean(testId),
    queryFn: async () =>
      unwrap(await api().GET('/topics/{topicId}/tests/{testId}', { params: { path: { topicId, testId: testId! } } })),
  });
}

export function useSavedTests() {
  return useQuery({ queryKey: qk.savedTests, queryFn: async () => unwrap(await api().GET('/tests')).groups });
}

export function useUpdateTest(topicId: string, testId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (exam: Exam) =>
      unwrap(await api().PUT('/topics/{topicId}/tests/{testId}', { params: { path: { topicId, testId } }, body: { exam } })),
    onSuccess: (t) => {
      qc.setQueryData(qk.test(topicId, testId), t);
      void qc.invalidateQueries({ queryKey: qk.topicTestsAll(topicId) });
      void qc.invalidateQueries({ queryKey: qk.savedTests });
    },
  });
}

export function useSaveTest(topicId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (testId: string) =>
      unwrap(await api().POST('/topics/{topicId}/tests/{testId}/save', { params: { path: { topicId, testId } } })),
    onSuccess: (t) => {
      qc.setQueryData(qk.test(topicId, t.id), t);
      void qc.invalidateQueries({ queryKey: qk.topicTestsAll(topicId) });
      void qc.invalidateQueries({ queryKey: qk.savedTests });
      void qc.invalidateQueries({ queryKey: qk.topic(topicId) });
    },
  });
}

export function useDeleteTest(topicId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (testId: string) =>
      unwrap(await api().DELETE('/topics/{topicId}/tests/{testId}', { params: { path: { topicId, testId } } })),
    onSuccess: (_r, testId) => {
      qc.removeQueries({ queryKey: qk.test(topicId, testId) });
      void qc.invalidateQueries({ queryKey: qk.topicTestsAll(topicId) });
      void qc.invalidateQueries({ queryKey: qk.savedTests });
      void qc.invalidateQueries({ queryKey: qk.topic(topicId) });
    },
  });
}

export function useRegenerateQuestion(topicId: string, testId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (questionId: string) =>
      unwrap(
        await api().POST('/topics/{topicId}/tests/{testId}/questions/{questionId}/regenerate', {
          params: { path: { topicId, testId, questionId } },
        }),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.activeJobs }),
  });
}

const EXT: Record<ExportRequest['format'], string> = {
  pdf: 'pdf',
  pdf_with_key: 'pdf',
  moodle_xml: 'xml',
  gift: 'txt',
  json: 'json',
};

function filenameFrom(res: Response, fallback: string): string {
  const cd = res.headers.get('content-disposition') ?? '';
  const star = /filename\*=UTF-8''([^;]+)/i.exec(cd);
  if (star) return decodeURIComponent(star[1]);
  const plain = /filename="?([^";]+)"?/i.exec(cd);
  return plain ? plain[1] : fallback;
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function useExportTest(topicId: string, test: Pick<Test, 'id' | 'title'>) {
  return useMutation({
    mutationFn: async (body: ExportRequest) => {
      const r = await api().POST('/topics/{topicId}/tests/{testId}/export', {
        params: { path: { topicId, testId: test.id } },
        body,
        parseAs: 'blob',
      });
      const blob = unwrap(r) as unknown as Blob;
      const safe = test.title.replace(/[^\p{L}\p{N}_-]+/gu, '_').slice(0, 60) || 'mimir-test';
      const multi = (body.variants ?? 1) > 1 && body.format.startsWith('pdf');
      downloadBlob(blob, filenameFrom(r.response, `${safe}.${multi ? 'zip' : EXT[body.format]}`));
    },
  });
}
