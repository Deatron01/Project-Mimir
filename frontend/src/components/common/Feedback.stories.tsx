import { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-vite';
import { Library } from 'lucide-react';
import ErrorNotice from './ErrorNotice';
import EmptyState from './EmptyState';
import ProgressBar from './ProgressBar';
import ConfirmDialog from './ConfirmDialog';
import Button from '../ui/Button';
import { ApiError } from '../../api/errors';

const meta: Meta = { title: 'Common/Feedback' };
export default meta;

export const Errors: StoryObj = {
  render: () => (
    <div className="flex max-w-xl flex-col gap-3">
      {(['FILE_TOO_LARGE', 'TOO_MANY_JOBS', 'LLM_UNAVAILABLE', 'NETWORK'] as const).map((code) => (
        <ErrorNotice key={code} error={new ApiError({ status: 400, code, requestId: 'req-123', details: { limit: 20 * 1048576 } })} onRetry={() => undefined} />
      ))}
    </div>
  ),
};
export const Empty: StoryObj = { render: () => <EmptyState icon={Library} title="Hozd létre az első témád" description="Leírás" action={<Button size="sm">Új téma</Button>} /> };
export const Progress: StoryObj = {
  render: () => (
    <div className="flex max-w-md flex-col gap-4">
      <ProgressBar value={0.35} label="35%" />
      <ProgressBar value={null} label="Queued" />
    </div>
  ),
};
function DialogDemo() {
  const [open, setOpen] = useState(true);
  return (
    <>
      <Button onClick={() => setOpen(true)}>Open</Button>
      <ConfirmDialog open={open} onClose={() => setOpen(false)} onConfirm={() => setOpen(false)} title="Törlöd ezt a témát?" body={<p>Ez nem vonható vissza.</p>} confirmLabel="Végleges törlés" danger typeToConfirm="Biológia" />
    </>
  );
}
export const DeleteConfirmation: StoryObj = { render: () => <DialogDemo /> };
