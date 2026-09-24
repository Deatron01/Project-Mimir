import type { Meta, StoryObj } from '@storybook/react-vite';
import TopicExplorer from './TopicExplorer';
import NewTopicModal from '../../components/topics/NewTopicModal';
import { api, applySession } from '../../api/client';
import { unwrap } from '../../api/errors';
import { DEMO_EMAIL, DEMO_PASSWORD } from '../../mocks/seed';

// Screens run against the in-browser mock API, signed in as the demo user.
const meta: Meta = {
  title: 'Screens/Topics',
  loaders: [
    async () => {
      applySession(unwrap(await api().POST('/auth/login', { body: { email: DEMO_EMAIL, password: DEMO_PASSWORD } })));
      return {};
    },
  ],
};
export default meta;
export const Explorer: StoryObj = { render: () => <TopicExplorer /> };
export const NewTopic: StoryObj = { render: () => <NewTopicModal open onClose={() => undefined} /> };
