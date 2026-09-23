import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import { unwrap } from '../errors';
import { qk } from '../keys';
import type { Language } from '../types';
import { useAuth } from '../../context/AuthContext';

export function useMe() {
  const { user } = useAuth();
  return useQuery({ queryKey: qk.me, enabled: Boolean(user), queryFn: async () => unwrap(await api().GET('/me')) });
}

export function useUpdateLanguage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (language: Language) => unwrap(await api().PATCH('/me', { body: { language } })),
    onSuccess: (me) => qc.setQueryData(qk.me, me),
  });
}

export function useExportMe() {
  return useMutation({ mutationFn: async () => unwrap(await api().POST('/me/export')) });
}

export function useDeleteMe() {
  return useMutation({ mutationFn: async (password: string) => unwrap(await api().DELETE('/me', { body: { password } })) });
}
