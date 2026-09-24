import { Cloud, HardDrive } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export interface ModelOption {
  id: string;
  label: string;
  location: 'external' | 'local';
}
export interface ModelList {
  local_only: boolean;
  external_available: boolean;
  default: string;
  models: ModelOption[];
  estimates_s?: Partial<Record<'external' | 'local', number>>;
}

export const AUTO_MODEL = 'auto';
export const MODEL_KEY = 'mimir-model';

export function loadModel(): string {
  try {
    return localStorage.getItem(MODEL_KEY) || AUTO_MODEL;
  } catch {
    return AUTO_MODEL;
  }
}
export function storeModel(id: string): void {
  try {
    if (id === AUTO_MODEL) localStorage.removeItem(MODEL_KEY);
    else localStorage.setItem(MODEL_KEY, id);
  } catch {
    /* ignore */
  }
}

/** Where the chosen model runs: "auto" uses the server when one is available, with the local model as fallback. */
export function locationOf(list: ModelList | undefined, id: string): 'external' | 'local' | null {
  if (!list) return null;
  if (id === AUTO_MODEL) return list.external_available ? 'external' : 'local';
  return list.models.find((m) => m.id === id)?.location ?? null;
}

/** A saved choice that the server no longer offers (e.g. LOCAL_ONLY switched on) falls back to "auto". */
export function validModel(list: ModelList | undefined, id: string): string {
  if (!list || id === AUTO_MODEL) return AUTO_MODEL;
  return list.models.some((m) => m.id === id) ? id : AUTO_MODEL;
}

/** FE-11: which model writes the test. Server models carry a "data leaves this machine" badge (GDPR-06). */
export default function ModelSelect({
  list,
  value,
  onChange,
  disabled,
  id = 'model-select',
}: {
  list: ModelList;
  value: string;
  onChange: (id: string) => void;
  disabled?: boolean;
  id?: string;
}) {
  const { t } = useTranslation();
  const server = list.models.filter((m) => m.location === 'external');
  const local = list.models.filter((m) => m.location === 'local');
  const where = locationOf(list, value);
  return (
    <div className="flex flex-wrap items-center gap-2">
      <label htmlFor={id} className="text-xs font-semibold uppercase tracking-wider text-muted">
        {t('models.label')}
      </label>
      <select
        id={id}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        aria-describedby={`${id}-where`}
        className="max-w-full rounded-full border border-border/60 bg-surface/60 px-3 py-1.5 text-sm text-textMain focus:outline-none focus:ring-2 focus:ring-accent/60"
      >
        <option value={AUTO_MODEL}>{list.external_available ? t('models.autoServer') : t('models.autoLocal')}</option>
        {server.length > 0 && (
          <optgroup label={t('models.groupServer')}>
            {server.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </optgroup>
        )}
        {local.length > 0 && (
          <optgroup label={t('models.groupLocal')}>
            {local.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </optgroup>
        )}
      </select>
      <span
        id={`${id}-where`}
        className={
          where === 'external'
            ? 'inline-flex items-center gap-1 rounded-full border border-warning/50 bg-warning/10 px-2 py-0.5 text-xs text-warning'
            : 'inline-flex items-center gap-1 rounded-full border border-success/50 bg-success/10 px-2 py-0.5 text-xs text-success'
        }
      >
        {where === 'external' ? <Cloud size={12} aria-hidden="true" /> : <HardDrive size={12} aria-hidden="true" />}
        {where === 'external' ? t('models.leavesMachine') : t('models.staysLocal')}
      </span>
    </div>
  );
}
