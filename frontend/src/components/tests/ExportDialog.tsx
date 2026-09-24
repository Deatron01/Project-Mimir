import { useState } from 'react';
import { Download } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Dialog from '../common/Dialog';
import Button from '../ui/Button';
import ErrorNotice from '../common/ErrorNotice';
import { useToast } from '../common/Toaster';
import { useExportTest } from '../../api/hooks/tests';
import type { ExportFormat } from '../../api/types';

const FORMATS: ExportFormat[] = ['pdf', 'pdf_with_key', 'moodle_xml', 'gift', 'json'];

/** Export options (TOP-14 / FE-06): PDF with or without key, Moodle XML, GIFT, JSON; A/B variants. */
export default function ExportDialog({ open, onClose, topicId, test }: { open: boolean; onClose: () => void; topicId: string; test: { id: string; title: string } }) {
  const { t } = useTranslation();
  const toast = useToast();
  const exp = useExportTest(topicId, test);
  const [format, setFormat] = useState<ExportFormat>('pdf');
  const [variants, setVariants] = useState<1 | 2>(1);
  const [shuffle, setShuffle] = useState(false);
  const isPdf = format === 'pdf' || format === 'pdf_with_key';

  const run = async () => {
    try {
      await exp.mutateAsync({ format, variants: isPdf ? variants : 1, shuffle_answers: shuffle });
      toast(t('export.done'));
      onClose();
    } catch {
      /* shown in dialog */
    }
  };

  return (
    <Dialog
      open={open}
      onClose={() => {
        exp.reset();
        onClose();
      }}
      busy={exp.isPending}
      title={t('export.title')}
      description={test.title}
      footer={
        <>
          <Button size="sm" variant="outline" onClick={onClose} disabled={exp.isPending}>
            {t('common.cancel')}
          </Button>
          <Button size="sm" onClick={() => void run()} isLoading={exp.isPending}>
            <Download size={14} aria-hidden="true" /> {t('export.download')}
          </Button>
        </>
      }
    >
      <fieldset className="mb-5">
        <legend className="mb-2 text-sm font-medium text-textMain">{t('export.format')}</legend>
        <div className="flex flex-col gap-2">
          {FORMATS.map((f) => (
            <div key={f} className="flex items-start gap-3 rounded-xl border border-border/40 p-3 hover:bg-surface/40 has-[:checked]:border-accent has-[:checked]:bg-accent/10">
              <input
                id={`export-${f}`}
                type="radio"
                name="export-format"
                value={f}
                checked={format === f}
                onChange={() => setFormat(f)}
                aria-describedby={`export-${f}-hint`}
                className="mt-1 h-4 w-4 accent-[rgb(var(--c-primary))]"
              />
              <div>
                <label htmlFor={`export-${f}`} className="block cursor-pointer text-sm font-medium text-textMain">
                  {t(`export.formats.${f}.label`)}
                </label>
                <span id={`export-${f}-hint`} className="block text-xs text-muted">
                  {t(`export.formats.${f}.hint`)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </fieldset>

      {isPdf && (
        <fieldset className="mb-4">
          <legend className="mb-2 text-sm font-medium text-textMain">{t('export.variants')}</legend>
          <div className="flex gap-4 text-sm">
            {([1, 2] as const).map((v) => (
              <label key={v} className="flex items-center gap-2">
                <input type="radio" name="export-variants" checked={variants === v} onChange={() => setVariants(v)} className="h-4 w-4 accent-[rgb(var(--c-primary))]" />
                {t(`export.variantOptions.${v}`)}
              </label>
            ))}
          </div>
        </fieldset>
      )}
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={shuffle} onChange={(e) => setShuffle(e.target.checked)} className="h-4 w-4 accent-[rgb(var(--c-primary))]" />
        {t('export.shuffle')}
      </label>
      {exp.isError && <ErrorNotice className="mt-4" error={exp.error} />}
    </Dialog>
  );
}
