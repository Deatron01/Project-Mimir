import { useQuery } from '@tanstack/react-query';
import { api } from '../client';
import { unwrap } from '../errors';
import { qk } from '../keys';
import { useAuth } from '../../context/AuthContext';

/** FE-11: models that can write a test, grouped by where they run. */
export function useModels() {
  const { user } = useAuth();
  return useQuery({
    queryKey: qk.models,
    enabled: Boolean(user),
    queryFn: async () => unwrap(await api().GET('/models')),
    staleTime: 5 * 60_000,
  });
}
