import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from './Dialog';
import Button from '../ui/Button';

interface Props {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  body: React.ReactNode;
  confirmLabel: string;
  danger?: boolean;
  busy?: boolean;
  /** If set, the user must type this text to enable the confirm button (used for topic deletion). */
  typeToConfirm?: string;
}

export default function ConfirmDialog({ open, onClose, onConfirm, title, body, confirmLabel, danger, busy, typeToConfirm }: Props) {
  const { t } = useTranslation();
  const [typed, setTyped] = useState('');
  const cancelRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const ok = !typeToConfirm || typed.trim() === typeToConfirm.trim();
  const close = () => {
    setTyped('');
    onClose();
  };
  return (
    <Dialog
      open={open}
      onClose={close}
      title={title}
      size="sm"
      role="alertdialog"
      busy={busy}
      initialFocusRef={typeToConfirm ? inputRef : cancelRef}
      footer={
        <>
          <Button ref={cancelRef} variant="outline" size="sm" onClick={close} disabled={busy}>
            {t('common.cancel')}
          </Button>
          <Button variant={danger ? 'danger' : 'primary'} size="sm" onClick={() => void onConfirm()} disabled={!ok} isLoading={busy}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-sm text-muted">{body}</div>
      {typeToConfirm && (
        <div className="mt-4">
          <label htmlFor="confirm-type" className="mb-1.5 block text-sm font-medium text-textMain">
            {t('common.typeToConfirm', { text: typeToConfirm })}
          </label>
          <input
            id="confirm-type"
            ref={inputRef}
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            className="field py-2"
            autoComplete="off"
          />
        </div>
      )}
    </Dialog>
  );
}
