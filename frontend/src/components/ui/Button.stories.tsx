import type { Meta, StoryObj } from '@storybook/react-vite';
import { Download } from 'lucide-react';
import Button from './Button';
import ButtonLink from './ButtonLink';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  args: { children: 'Mentés' },
  argTypes: { variant: { control: 'select', options: ['primary', 'secondary', 'outline', 'ghost', 'danger'] }, size: { control: 'select', options: ['sm', 'md', 'lg', 'icon'] } },
};
export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {};
export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-3">
      {(['primary', 'secondary', 'outline', 'ghost', 'danger'] as const).map((v) => (
        <Button key={v} variant={v}>
          {v}
        </Button>
      ))}
      <Button isLoading>Loading</Button>
      <Button disabled>Disabled</Button>
      <Button size="sm" variant="outline">
        <Download size={14} aria-hidden="true" /> Export
      </Button>
      <ButtonLink to="/topics" variant="primary" size="sm">
        Link as button
      </ButtonLink>
    </div>
  ),
};
