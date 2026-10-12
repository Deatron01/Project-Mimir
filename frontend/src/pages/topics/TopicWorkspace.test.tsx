import { describe, expect, it } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TopicWorkspace from './TopicWorkspace';
import { api } from '../../api/client';
import { unwrap } from '../../api/errors';
import { loginDemo, renderRoutes } from '../../test/utils';

describe('TopicWorkspace class switcher', () => {
  it('lists every class and switches class while keeping the current tab', async () => {
    await loginDemo();
    const geo = unwrap(await api().POST('/topics', { body: { name: 'Geography' } }));
    const { router } = renderRoutes([{ path: '/topics/:topicId/*', element: <TopicWorkspace /> }], { initialPath: '/topics/top_demo/files' });

    expect(await screen.findByRole('heading', { level: 1, name: 'Fotoszintézis (demo)' })).toBeInTheDocument();
    const sidebar = screen.getByRole('complementary', { name: 'My classes' });
    const current = await within(sidebar).findByRole('link', { name: /Fotoszintézis \(demo\)/ });
    expect(current).toHaveAttribute('aria-current', 'page');

    const target = within(sidebar).getByRole('link', { name: /Geography/ });
    expect(target).toHaveAttribute('href', `/topics/${geo.id}/files`);
    await userEvent.click(target);

    expect(await screen.findByRole('heading', { level: 1, name: 'Geography' })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe(`/topics/${geo.id}/files`);
  });
});
