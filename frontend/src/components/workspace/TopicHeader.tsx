import { useRef, useState } from 'react';
import { Check, Hourglass, Pencil, Radio, Trash2, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '../ui/Button';
import ConfirmDialog from '../common/ConfirmDialog';
import { useErrorText } from '../common/ErrorNotice';
import { useToast } from '../common/Toaster';
import { useDeleteTopic, useUpdateTopic } from '../../api/hooks/topics';
import { useTopicStreamState } from '../../api/TopicStream';
import type { Topic } from '../../api/types';
import { formatBytes, formatDate } from '../../utils/format';
import { cn } from '../../utils/cn';

/** Topic header: inline rename/description edit, usage, auto-deletion date, live status and delete. */
export default function TopicHeader({ topic }: { topic: Topic }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? 'hu';
  const navigate = useNavigate();
  const toast = useToast();
  const errorText = useErrorText();
  const update = useUpdateTopic(topic.id);
  const del = useDeleteTopic();
  const stream = useTopicStreamState();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(topic.name);
  const [description, setDescription] = useState(topic.description);
  const [confirm, setConfirm] = useState(false);
  const editBtn = useRef<HTMLButtonElement>(null);

  const startEdit = () => {
    setName(topic.name);
    setDescription(topic.description);
    setEditing(true);
  };
  const cancel = () => {
    setEditing(false);
    requestAnimationFrame(() => editBtn.current?.focus());
  };
  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await update.mutateAsync({ name: name.trim(), description: description.trim() });
      setEditing(false);
      toast(t('workspace.header.saved'));
      requestAnimationFrame(() => editBtn.current?.focus());
    } catch (err) {
      toast(errorText(err), 'error');
    }
  };
  const remove = async () => {
    try {
      await del.mutateAsync(topic.id);
      setConfirm(false);
      toast(t('workspace.header.deleteStarted', { name: topic.name }));
      navigate('/topics', { replace: true });
    } catch (err) {
      toast(errorText(err), 'error');
    }
  };

  return (
    <header className="card p-5 md:p-6">
      {editing ? (
        <form onSubmit={save} className="flex flex-col gap-3" aria-label={t('workspace.header.editLabel')}>
          <label htmlFor="edit-topic-name" className="sr-only">
            {t('topics.fields.name')}
          </label>
          <input
            id="edit-topic-name"
            value={name}
            maxLength={80}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === 'Escape' && cancel()}
            className="field py-2 text-xl font-bold"
            required
            // eslint-disable-next-line jsx-a11y/no-autofocus -- the user just pressed "edit"; focus belongs here
            autoFocus
          />
          <label htmlFor="edit-topic-desc" className="sr-only">
            {t('topics.fields.description')}
          </label>
          <textarea
            id="edit-topic-desc"
            value={description}
            maxLength={500}
            rows={2}
            onChange={(e) => setDescription(e.target.value)}
            onKeyDown={(e) => e.key === 'Escape' && cancel()}
            placeholder={t('topics.fields.descriptionPlaceholder')}
            className="field resize-y py-2 text-sm"
          />
          <div className="flex gap-2">
            <Button size="sm" type="submit" isLoading={update.isPending} disabled={!name.trim()}>
              <Check size={14} aria-hidden="true" /> {t('common.save')}
            </Button>
            <Button size="sm" variant="outline" onClick={cancel}>
              <X size={14} aria-hidden="true" /> {t('common.cancel')}
            </Button>
          </div>
        </form>
      ) : (
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="min-w-0">
            <h1 className="break-words text-2xl font-extrabold tracking-tight md:text-3xl">{topic.name}</h1>
            {topic.description && <p className="mt-1 max-w-3xl text-sm text-muted">{topic.description}</p>}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Button ref={editBtn} size="sm" variant="outline" onClick={startEdit}>
              <Pencil size={14} aria-hidden="true" /> {t('common.edit')}
            </Button>
            <Button size="sm" variant="danger" onClick={() => setConfirm(true)}>
              <Trash2 size={14} aria-hidden="true" /> {t('workspace.header.delete')}
            </Button>
          </div>
        </div>
      )}

      <dl className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs text-muted">
        <div className="flex gap-1">
          <dt>{t('topics.stats.files')}:</dt>
          <dd className="font-medium text-textMain">{topic.file_count}</dd>
        </div>
        <div className="flex gap-1">
          <dt>{t('workspace.header.storage')}:</dt>
          <dd className="font-medium text-textMain">{formatBytes(topic.total_bytes, lang)}</dd>
        </div>
        <div className="flex gap-1">
          <dt>{t('topics.stats.saved')}:</dt>
          <dd className="font-medium text-textMain">{topic.saved_test_count}</dd>
        </div>
        <div className="flex items-center gap-1" title={t('workspace.header.expiryHelp')}>
          <Hourglass size={12} aria-hidden="true" />
          <dt>{t('workspace.header.expires')}:</dt>
          <dd className="font-medium text-textMain">{formatDate(topic.expires_at, lang, { dateStyle: 'medium' })}</dd>
        </div>
        <div className="flex items-center gap-1">
          <Radio size={12} aria-hidden="true" className={cn(stream === 'open' ? 'text-success' : 'text-warning')} />
          <dt className="sr-only">{t('workspace.header.live')}</dt>
          <dd>{t(`workspace.stream.${stream}`)}</dd>
        </div>
      </dl>

      <ConfirmDialog
        open={confirm}
        onClose={() => setConfirm(false)}
        onConfirm={remove}
        busy={del.isPending}
        danger
        title={t('workspace.header.deleteTitle')}
        confirmLabel={t('workspace.header.deleteConfirm')}
        typeToConfirm={topic.name}
        body={
          <>
            <p>{t('workspace.header.deleteBody', { files: topic.file_count, saved: topic.saved_test_count })}</p>
            <p>{t('workspace.header.deleteCrypto')}</p>
          </>
        }
      />
    </header>
  );
}
