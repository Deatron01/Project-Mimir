import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createMemoryRouter, RouterProvider, type RouteObject } from 'react-router-dom';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import { ToastProvider } from '../components/common/Toaster';
import { api, applySession } from '../api/client';
import { unwrap } from '../api/errors';
import { DEMO_EMAIL, DEMO_PASSWORD } from '../mocks/seed';

export function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 0 }, mutations: { retry: false } } });
}

/** Renders routes inside every app provider, on a memory router. */
export function renderRoutes(routes: RouteObject[], { initialPath = '/' }: { initialPath?: string } = {}) {
  const qc = makeQueryClient();
  const router = createMemoryRouter(routes, { initialEntries: [initialPath] });
  const utils = render(
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <ThemeProvider>
          <ToastProvider>
            <RouterProvider router={router} />
          </ToastProvider>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>,
  );
  return { ...utils, router, qc };
}

export const renderUi = (ui: React.ReactNode, path = '/') => renderRoutes([{ path: '*', element: ui }], { initialPath: path });

/** Logs the seeded demo user in against the mock API (sets the in-memory access token). */
export async function loginDemo() {
  const session = unwrap(await api().POST('/auth/login', { body: { email: DEMO_EMAIL, password: DEMO_PASSWORD } }));
  applySession(session);
  return session;
}
