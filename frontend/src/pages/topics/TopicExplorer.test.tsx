import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TopicExplorer from './TopicExplorer';
import { loginDemo, renderRoutes } from '../../test/utils';

describe('TopicExplorer', () => {
  it('lists topics and filters by search', async () => {
    await loginDemo();
    renderRoutes([{ path: '/topics', element: <TopicExplorer /> }], { initialPath: '/topics' });
    expect(await screen.findByRole('link', { name: /Fotoszintézis \(demo\)/ })).toBeInTheDocument();
    expect(screen.getByText('1 of 50 topics')).toBeInTheDocument();
    await userEvent.type(screen.getByRole('searchbox', { name: 'Search topics' }), 'zzz');
    expect(await screen.findByText('No topic matches “zzz”.')).toBeInTheDocument();
  });
});
