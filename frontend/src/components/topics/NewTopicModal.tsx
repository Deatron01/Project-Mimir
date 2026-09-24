import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Dialog from '../common/Dialog';
import Dropzone from './Dropzone';
import Button from '../ui/Button';
import ErrorNotice, { useErrorText } from '../common/ErrorNotice';
import ProgressBar from '../common/ProgressBar';
import { useToast } from '../common/Toaster';
import { useCreateTopic } from '../../api/hooks/topics';
import { uploadFiles } from '../../api/upload';
import type { Limits } from '../../api/types';

const NAME_MAX = 80;
const DESC_MAX = 500;

/** "New topic" dialog (TOP-11): name, optional description and optional first documents. */
export default function NewTopicModal({ open, onClose, limits }: { open: boolean; onClose: () => void; limits?: Limits }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const toast = useToast();
  const errorText = useErrorText();
  const create = useCreateTopic();
  const nameRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [consent, setConsent] = useState(false);
  const [touched, setTouched] = useState(false);
  const [consentError, setConsentError] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<unknown>(null);
  const busy = create.isPending || progress !== null;

  const reset = () => {
    setName('');
    setDescription('');
    setFiles([]);
    setConsent(false);
    setTouched(false);
    setConsentError(false);
    setProgress(null);
    setError(null);
    create.reset();
  };
  const close = () => {
    if (busy) return;
    reset();
    onClose();
  };

  const nameError = touched && !name.trim() ? t('topics.new.nameRequired') : '';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    setError(null);
    if (!name.trim()) {
      nameRef.current?.focus();
      return;
    }
    if (files.length && !consent) {
      setConsentError(true);
      return;
    }
    let topicId: string;
    try {
      const topic = await create.mutateAsync({ name: name.trim(), description: description.trim() || undefined });
      topicId = topic.id;
    } catch (err) {
      setError(err);
      return;
    }
    if (files.length) {
      setProgress(0);
      try {
        await uploadFiles(topicId, files, { onProgress: setProgress });
      } catch (err) {
        // The topic exists already – open it and let the user retry the upload there.
        toast(t('topics.new.uploadFailed', { reason: errorText(err) }), 'error');
      }
    }
    toast(t('topics.new.created', { name: name.trim() }));
    reset();
    onClose();
    navigate(`/topics/${topicId}${files.length ? '/files' : ''}`);
  };

  return (
    <Dialog
      open={open}
      onClose={close}
      busy={busy}
      title={t('topics.new.title')}
      description={t('topics.new.subtitle')}
      size="lg"
      initialFocusRef={nameRef}
      footer={
        <>
          <Button variant="outline" size="sm" onClick={close} disabled={busy}>
            {t('common.cancel')}
          </Button>
          <Button size="sm" type="submit" form="new-topic-form" isLoading={busy}>
            {files.length ? t('topics.new.createAndUpload') : t('topics.new.create')}
          </Button>
        </>
      }
    >
      <form id="new-topic-form" onSubmit={submit} noValidate className="flex flex-col gap-5">
        <div>
          <label htmlFor="topic-name" className="mb-1.5 block text-sm font-medium text-textMain">
            {t('topics.fields.name')} <span aria-hidden="true" className="text-danger">*</span>
          </label>
          <input
            id="topic-name"
            ref={nameRef}
            value={name}
            maxLength={NAME_MAX}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => setTouched(true)}
            required
            aria-required="true"
            aria-invalid={Boolean(nameError) || undefined}
            aria-describedby="topic-name-hint topic-name-error"
            placeholder={t('topics.fields.namePlaceholder')}
            className="field py-2.5"
            disabled={busy}
          />
          <div className="mt-1 flex justify-between text-xs">
            <span id="topic-name-error" className="text-danger">
              {nameError}
            </span>
            <span id="topic-name-hint" className="text-muted">
              {t('common.charCount', { count: name.length, max: NAME_MAX })}
            </span>
          </div>
        </div>

        <div>
          <label htmlFor="topic-desc" className="mb-1.5 block text-sm font-medium text-textMain">
            {t('topics.fields.description')} <span className="text-xs font-normal text-muted">({t('common.optional')})</span>
          </label>
          <textarea
            id="topic-desc"
            value={description}
            maxLength={DESC_MAX}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder={t('topics.fields.descriptionPlaceholder')}
            className="field resize-y py-2.5"
            disabled={busy}
            aria-describedby="topic-desc-count"
          />
          <p id="topic-desc-count" className="mt-1 text-right text-xs text-muted">
            {t('common.charCount', { count: description.length, max: DESC_MAX })}
          </p>
        </div>

        <fieldset>
          <legend className="mb-1.5 text-sm font-medium text-textMain">
            {t('topics.new.documents')} <span className="text-xs font-normal text-muted">({t('common.optional')})</span>
          </legend>
          <Dropzone
            files={files}
            onFilesChange={setFiles}
            consent={consent}
            onConsentChange={(v) => {
              setConsent(v);
              setConsentError(false);
            }}
            consentError={consentError}
            limits={limits}
            disabled={busy}
          />
        </fieldset>

        {progress !== null && <ProgressBar value={progress} label={t('upload.progress', { pct: Math.round(progress * 100) })} />}
        <ErrorNotice error={error} />
      </form>
    </Dialog>
  );
}
