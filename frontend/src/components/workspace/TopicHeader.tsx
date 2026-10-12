import { useRef, useState } from 'react';
import { Check, FileText, HardDrive, Hourglass, Pencil, Star, Trash2, X, type LucideIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '../ui/Button';
import HelpTip from '../ui/HelpTip';
import ClassAvatar from '../topics/ClassAvatar';
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
    <header className="card p-4 sm:p-5 md:p-6">
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
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-4">
            <ClassAvatar name={topic.name} size="lg" className="hidden sm:flex" />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <h1 className="min-w-0 break-words text-xl font-extrabold tracking-tight sm:text-2xl md:text-3xl">{topic.name}</h1>
                <HelpTip label={topic.name} size={16}>
                  {t('help.class')}
                </HelpTip>
              </div>
              {topic.description && <p className="mt-1 line-clamp-2 max-w-3xl text-sm text-muted sm:line-clamp-none">{topic.description}</p>}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {/* Icon-only on phones; the accessible name stays the full label. */}
            <Button ref={editBtn} size="sm" variant="outline" onClick={startEdit} aria-label={t('common.edit')} className="w-10 px-0 sm:w-auto sm:px-4">
              <Pencil size={14} aria-hidden="true" /> <span className="hidden sm:inline">{t('common.edit')}</span>
            </Button>
            <Button size="sm" variant="danger" onClick={() => setConfirm(true)} aria-label={t('workspace.header.delete')} className="w-10 px-0 sm:w-auto sm:px-4">
              <Trash2 size={14} aria-hidden="true" /> <span className="hidden sm:inline">{t('workspace.header.delete')}</span>
            </Button>
          </div>
        </div>
      )}

      <ul aria-label={t('workspace.header.stats')} className="relative -mx-4 mt-3 flex gap-2 overflow-x-auto px-4 pb-1 text-xs text-muted sm:mx-0 sm:mt-4 sm:flex-wrap sm:overflow-visible sm:px-0 sm:pb-0">
        <Stat icon={FileText} label={t('topics.stats.files')} value={topic.file_count} />
        <Stat icon={HardDrive} label={t('workspace.header.storage')} value={formatBytes(topic.total_bytes, lang)} help={t('help.storage')} />
        <Stat icon={Star} label={t('topics.stats.saved')} value={topic.saved_test_count} />
        <Stat
          icon={Hourglass}
          label={t('workspace.header.expires')}
          value={formatDate(topic.expires_at, lang, { dateStyle: 'medium' })}
          help={t('workspace.header.expiryHelp')}
        />
        <li className="flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border border-border/40 bg-background/40 py-1 pl-3 pr-1">
          <span className={cn('relative flex h-2 w-2', stream === 'open' ? 'text-success' : 'text-warning')} aria-hidden="true">
            {stream === 'open' && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-current opacity-60" />}
            <span className="relative inline-flex h-2 w-2 rounded-full bg-current" />
          </span>
          <span className="sr-only">{t('workspace.header.live')}:</span>
          <span className="font-medium text-textMain">{t(`workspace.stream.${stream}`)}</span>
          <HelpTip label={t('workspace.header.live')} size={13}>
            {t('help.live')}
          </HelpTip>
        </li>
      </ul>

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

function Stat({ icon: Icon, label, value, help }: { icon: LucideIcon; label: string; value: React.ReactNode; help?: string }) {
  return (
    <li className={cn('flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border border-border/40 bg-background/40 py-1 pl-3', help ? 'pr-1' : 'pr-3')}>
      <Icon size={13} aria-hidden="true" />
      <span>{label}:</span>
      <span className="font-semibold text-textMain">{value}</span>
      {help && (
        <HelpTip label={label} size={13}>
          {help}
        </HelpTip>
      )}
    </li>
  );
}
