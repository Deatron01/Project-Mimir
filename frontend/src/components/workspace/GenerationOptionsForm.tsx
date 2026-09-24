import { useTranslation } from 'react-i18next';
import SegmentedControl from '../ui/SegmentedControl';
import ModelSelect, { AUTO_MODEL, validModel } from '../generation/ModelSelect';
import { useModels } from '../../api/hooks/models';
import type { GenerationOptions, QuestionType, TopicFile } from '../../api/types';

export const OPTIONS_KEY = 'mimir-gen-options';

export function loadOptions(lang: 'hu' | 'en'): GenerationOptions {
  const fallback: GenerationOptions = { count: 10, types: ['mcq', 'tf'], difficulty: 'medium', exam_language: lang, mode: 'fast' };
  try {
    const raw = JSON.parse(localStorage.getItem(OPTIONS_KEY) || 'null') as Partial<GenerationOptions> | null;
    if (!raw) return fallback;
    const { file_ids: _ignored, ...rest } = raw;
    return { ...fallback, ...rest };
  } catch {
    return fallback;
  }
}
export function storeOptions(o: GenerationOptions): void {
  try {
    const { file_ids: _ignored, ...rest } = o;
    localStorage.setItem(OPTIONS_KEY, JSON.stringify(rest));
  } catch {
    /* ignore */
  }
}

const TYPES: QuestionType[] = ['mcq', 'tf', 'open'];

/** Generation settings shown under the chat composer (FE-05: the old wizard, folded into the topic chat). */
export default function GenerationOptionsForm({
  value,
  onChange,
  readyFiles,
  disabled,
}: {
  value: GenerationOptions;
  onChange: (v: GenerationOptions) => void;
  readyFiles: TopicFile[];
  disabled?: boolean;
}) {
  const { t } = useTranslation();
  const models = useModels();
  const set = (patch: Partial<GenerationOptions>) => onChange({ ...value, ...patch });
  const toggleType = (type: QuestionType) => {
    const types = value.types.includes(type) ? value.types.filter((x) => x !== type) : [...value.types, type];
    if (types.length) set({ types });
  };
  const allFiles = !value.file_ids?.length;
  const toggleFile = (id: string) => {
    const cur = value.file_ids?.length ? value.file_ids : readyFiles.map((f) => f.id);
    const next = cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id];
    set({ file_ids: next.length === readyFiles.length || !next.length ? undefined : next });
  };

  return (
    <fieldset disabled={disabled} className="grid gap-4 rounded-2xl border border-border/40 bg-surface/30 p-4 text-sm sm:grid-cols-2">
      <legend className="sr-only">{t('generate.legend')}</legend>
      <div>
        <label htmlFor="gen-count" className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted">
          {t('generate.count')}
        </label>
        <input
          id="gen-count"
          type="number"
          min={1}
          max={50}
          value={value.count}
          onChange={(e) => set({ count: Math.max(1, Math.min(50, Number(e.target.value) || 1)) })}
          className="field w-28 py-1.5"
        />
      </div>

      <div>
        <span id="gen-types" className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted">
          {t('generate.types')}
        </span>
        <div role="group" aria-labelledby="gen-types" className="flex flex-wrap gap-3">
          {TYPES.map((type) => (
            <label key={type} className="flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={value.types.includes(type)}
                onChange={() => toggleType(type)}
                className="h-4 w-4 accent-[rgb(var(--c-primary))]"
              />
              {t(`editor.types.${type}`)}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label htmlFor="gen-difficulty" className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted">
          {t('generate.difficulty')}
        </label>
        <select
          id="gen-difficulty"
          value={value.difficulty}
          onChange={(e) => set({ difficulty: e.target.value as GenerationOptions['difficulty'] })}
          className="rounded-full border border-border/60 bg-surface/60 px-3 py-1.5 text-sm text-textMain focus:outline-none focus:ring-2 focus:ring-accent/60"
        >
          {(['easy', 'medium', 'hard'] as const).map((d) => (
            <option key={d} value={d}>
              {t(`editor.difficulty.${d}`)}
            </option>
          ))}
        </select>
      </div>

      <div>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted">{t('generate.examLanguage')}</span>
        <SegmentedControl
          label={t('generate.examLanguage')}
          value={value.exam_language}
          onChange={(exam_language) => set({ exam_language })}
          options={[
            { value: 'hu', label: 'Magyar' },
            { value: 'en', label: 'English' },
          ]}
          className="max-w-xs"
        />
      </div>

      <div className="sm:col-span-2">
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted">{t('generate.mode')}</span>
        <SegmentedControl
          label={t('generate.mode')}
          value={value.mode}
          onChange={(mode) => set({ mode })}
          options={[
            { value: 'fast', label: t('generate.modes.fast') },
            { value: 'thorough', label: t('generate.modes.thorough') },
          ]}
          className="max-w-sm"
        />
        <p className="mt-1 text-xs text-muted">{t(`generate.modeHint.${value.mode}`)}</p>
      </div>

      {models.data && (
        <div className="sm:col-span-2">
          <ModelSelect
            id="gen-model"
            list={models.data}
            value={validModel(models.data, value.model ?? AUTO_MODEL)}
            onChange={(model) => set({ model: model === AUTO_MODEL ? undefined : model })}
          />
        </div>
      )}

      {readyFiles.length > 1 && (
        <div className="sm:col-span-2">
          <span id="gen-files" className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted">
            {t('generate.sources')} {allFiles && <span className="font-normal normal-case">({t('generate.allFiles')})</span>}
          </span>
          <div role="group" aria-labelledby="gen-files" className="flex flex-col gap-1.5">
            {readyFiles.map((f) => (
              <label key={f.id} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={allFiles || value.file_ids!.includes(f.id)}
                  onChange={() => toggleFile(f.id)}
                  className="h-4 w-4 accent-[rgb(var(--c-primary))]"
                />
                <span className="truncate">{f.filename}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </fieldset>
  );
}
