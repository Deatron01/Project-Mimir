import { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-vite';
import Dropzone from './Dropzone';
import FileStatusBadge from './FileStatusBadge';

const meta: Meta<typeof Dropzone> = { title: 'Topics/Dropzone', component: Dropzone };
export default meta;

function Stateful({ consentError = false }: { consentError?: boolean }) {
  const [files, setFiles] = useState<File[]>([new File(['x'.repeat(2048)], 'jegyzet.pdf')]);
  const [consent, setConsent] = useState(false);
  return <Dropzone files={files} onFilesChange={setFiles} consent={consent} onConsentChange={setConsent} consentError={consentError} />;
}

export const WithFile: StoryObj = { render: () => <Stateful /> };
export const ConsentMissing: StoryObj = { render: () => <Stateful consentError /> };
export const StatusBadges: StoryObj = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      {(['queued', 'extracting', 'chunking', 'indexing', 'ready', 'failed'] as const).map((s) => (
        <FileStatusBadge key={s} status={s} />
      ))}
    </div>
  ),
};
