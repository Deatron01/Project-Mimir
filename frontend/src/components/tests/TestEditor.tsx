import { forwardRef, useEffect, useImperativeHandle, useMemo, useRef, useState } from 'react';
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type Announcements,
  type DragEndEvent,
} from '@dnd-kit/core';
import { SortableContext, arrayMove, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { ArrowDown, ArrowUp, BookOpen, CheckCircle2, CheckSquare, GripVertical, Plus, RefreshCw, Trash2, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Button from '../ui/Button';
import { cn } from '../../utils/cn';
import type { Answer, Citation, Difficulty, Exam, Question, QuestionType } from '../../api/types';

const TYPES: QuestionType[] = ['mcq', 'tf', 'open'];
const MAX_ANSWERS = 6;
let uid = 0;
const localId = () => `new_${Date.now().toString(36)}${(uid += 1)}`;

/** Input shape: legacy results have no ids, citations or difficulty. */
export interface EditableExam {
  title?: string;
  questions?: Array<Partial<Question> & { text?: string; answers?: Partial<Answer>[] }>;
}
interface DraftQuestion extends Question {
  _key: string;
}
interface Draft {
  title: string;
  questions: DraftQuestion[];
}

const toDraftQuestion = (q: EditableExam['questions'] extends (infer T)[] | undefined ? T : never): DraftQuestion => {
  const id = q.id ?? localId();
  return {
    id,
    _key: id,
    type: TYPES.includes(q.type as QuestionType) ? (q.type as QuestionType) : 'mcq',
    text: q.text ?? '',
    answers: (q.answers ?? []).map((a) => ({ text: a.text ?? '', is_correct: Boolean(a.is_correct) })),
    citations: q.citations ?? [],
    difficulty: (q.difficulty as Difficulty) ?? 'medium',
  };
};
const toDraft = (data: EditableExam): Draft => ({ title: data.title ?? '', questions: (data.questions ?? []).map(toDraftQuestion) });

const fromDraft = (d: Draft): Exam => ({
  title: d.title.trim(),
  questions: d.questions.map(({ _key: _k, ...q }) => ({
    ...q,
    text: q.text.trim(),
    answers: q.answers.map((a) => ({ text: a.text.trim(), is_correct: a.is_correct })),
  })),
});

export interface TestEditorHandle {
  /** Swaps in a regenerated question while keeping the user's other unsaved edits. */
  replaceQuestion: (q: Question) => void;
  getExam: () => Exam;
}

export interface TestEditorProps {
  initial: EditableExam;
  onSubmit: (exam: Exam, opts: { save: boolean }) => void | Promise<void>;
  submitLabel?: string;
  disabled?: boolean;
  /** Shows the opt-in "save to my tests" box (privacy by default: unchecked). */
  canSave?: boolean;
  onRegenerate?: (questionId: string) => void;
  regeneratingIds?: ReadonlySet<string>;
  /** file_id → filename, for citation labels. */
  fileNames?: Record<string, string>;
  onDirtyChange?: (dirty: boolean) => void;
  /** Extra actions rendered next to the submit button (e.g. export menu). */
  actions?: React.ReactNode;
}

/**
 * Structured editor for a generated test – the human review step required before use (EU AI Act art. 14).
 * Questions can be reordered by drag and drop (mouse, touch, or keyboard: Space to lift, arrows to move),
 * regenerated one by one, and show the source passages they were generated from.
 */
const TestEditor = forwardRef<TestEditorHandle, TestEditorProps>(function TestEditor(
  { initial, onSubmit, submitLabel, disabled, canSave = false, onRegenerate, regeneratingIds, fileNames, onDirtyChange, actions },
  ref,
) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState<Draft>(() => toDraft(initial));
  const [errors, setErrors] = useState<string[]>([]);
  const [save, setSave] = useState(false);
  const [dirty, setDirty] = useState(false);
  const errorRef = useRef<HTMLDivElement>(null);

  useEffect(() => onDirtyChange?.(dirty), [dirty, onDirtyChange]);

  const change = (fn: (d: Draft) => Draft) => {
    setDraft(fn);
    setDirty(true);
  };
  const update = (fn: (qs: DraftQuestion[]) => DraftQuestion[]) => change((d) => ({ ...d, questions: fn(d.questions) }));
  const patchQuestion = (key: string, patch: Partial<DraftQuestion>) =>
    update((qs) => qs.map((q) => (q._key === key ? { ...q, ...patch } : q)));

  useImperativeHandle(
    ref,
    () => ({
      replaceQuestion: (q) =>
        setDraft((d) => ({ ...d, questions: d.questions.map((x) => (x.id === q.id ? { ...toDraftQuestion(q), _key: x._key } : x)) })),
      getExam: () => fromDraft(draft),
    }),
    [draft],
  );

  const changeType = (q: DraftQuestion, type: QuestionType) => {
    let answers = q.answers;
    const correct = q.answers.find((a) => a.is_correct)?.text ?? '';
    if (type === 'tf') {
      answers = [
        { text: t('editor.true'), is_correct: true },
        { text: t('editor.false'), is_correct: false },
      ];
    } else if (type === 'open') {
      answers = [{ text: correct, is_correct: true }];
    } else {
      answers = [...q.answers];
      while (answers.length < 4) answers.push({ text: '', is_correct: false });
      if (!answers.some((a) => a.is_correct)) answers[0] = { ...answers[0], is_correct: true };
    }
    patchQuestion(q._key, { type, answers });
  };

  const setAnswer = (q: DraftQuestion, idx: number, patch: Partial<Answer>) =>
    patchQuestion(q._key, { answers: q.answers.map((a, i) => (i === idx ? { ...a, ...patch } : a)) });
  const markCorrect = (q: DraftQuestion, idx: number) =>
    patchQuestion(q._key, { answers: q.answers.map((a, i) => ({ ...a, is_correct: i === idx })) });
  const removeAnswer = (q: DraftQuestion, idx: number) => {
    const answers = q.answers.filter((_, i) => i !== idx);
    if (!answers.some((a) => a.is_correct) && answers.length) answers[0] = { ...answers[0], is_correct: true };
    patchQuestion(q._key, { answers });
  };
  const move = (idx: number, dir: -1 | 1) => update((qs) => arrayMove(qs, idx, idx + dir));

  const addQuestion = () =>
    update((qs) => {
      const id = localId();
      return [
        ...qs,
        { id, _key: id, type: 'mcq', text: '', answers: [0, 1, 2, 3].map((i) => ({ text: '', is_correct: i === 0 })), citations: [], difficulty: 'medium' },
      ];
    });

  const validate = () => {
    const errs: string[] = [];
    if (!draft.title.trim()) errs.push(t('editor.validation.title'));
    if (!draft.questions.length) errs.push(t('editor.validation.noQuestions'));
    draft.questions.forEach((q, i) => {
      const n = i + 1;
      if (!q.text.trim()) errs.push(t('editor.validation.emptyQuestion', { n }));
      if (q.type !== 'open' && q.answers.length < 2) errs.push(t('editor.validation.minAnswers', { n }));
      if (q.answers.some((a) => !a.text.trim())) errs.push(t('editor.validation.emptyAnswer', { n }));
      if (q.type !== 'open' && q.answers.filter((a) => a.is_correct).length !== 1) errs.push(t('editor.validation.oneCorrect', { n }));
    });
    return errs;
  };

  const handleSubmit = async () => {
    const errs = validate();
    setErrors(errs);
    if (errs.length) {
      requestAnimationFrame(() => errorRef.current?.focus());
      return;
    }
    await onSubmit(fromDraft(draft), { save });
    setDirty(false);
  };

  // --- drag & drop
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const indexOfKey = (k: string | number) => draft.questions.findIndex((q) => q._key === k) + 1;
  const announcements: Announcements = {
    onDragStart: ({ active }) => t('editor.dnd.picked', { n: indexOfKey(active.id) }),
    onDragOver: ({ active, over }) => (over ? t('editor.dnd.over', { n: indexOfKey(active.id), pos: indexOfKey(over.id) }) : undefined),
    onDragEnd: ({ active, over }) => (over ? t('editor.dnd.dropped', { n: indexOfKey(active.id), pos: indexOfKey(over.id) }) : undefined),
    onDragCancel: ({ active }) => t('editor.dnd.cancelled', { n: indexOfKey(active.id) }),
  };
  const onDragEnd = ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return;
    update((qs) => arrayMove(qs, qs.findIndex((q) => q._key === active.id), qs.findIndex((q) => q._key === over.id)));
  };

  const count = draft.questions.length;
  const typeOptions = useMemo(() => TYPES.map((type) => ({ value: type, label: t(`editor.types.${type}`) })), [t]);

  return (
    <div className="rounded-xl border border-accent/40 bg-surface/80 p-4 shadow-inner md:p-5">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-accent">
          <CheckSquare size={16} aria-hidden="true" />
          <span>{t('editor.title')}</span>
        </div>
        <span className="text-xs text-muted">{t('editor.questionCount', { count })}</span>
      </div>
      <p className="mb-4 text-xs text-muted">{t('editor.hint')}</p>

      <label htmlFor="exam-title" className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted">
        {t('editor.examTitle')}
      </label>
      <input
        id="exam-title"
        value={draft.title}
        onChange={(e) => change((d) => ({ ...d, title: e.target.value }))}
        className="field mb-5 py-2"
        disabled={disabled}
      />

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={onDragEnd}
        accessibility={{ announcements, screenReaderInstructions: { draggable: t('editor.dnd.instructions') } }}
      >
        <SortableContext items={draft.questions.map((q) => q._key)} strategy={verticalListSortingStrategy}>
          <ol className="flex flex-col gap-4">
            {draft.questions.map((q, idx) => (
              <SortableQuestion key={q._key} id={q._key} disabled={disabled}>
                {(handle) => (
                  <>
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-1">
                        {handle}
                        <span className="text-sm font-bold">{t('editor.question', { n: idx + 1 })}</span>
                        <span className="ml-2 rounded-full border border-border/50 px-2 py-0.5 text-[11px] text-muted">
                          {t(`editor.difficulty.${q.difficulty}`)}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <label className="sr-only" htmlFor={`${q._key}-type`}>
                          {t('editor.type')}
                        </label>
                        <select
                          id={`${q._key}-type`}
                          value={q.type}
                          onChange={(e) => changeType(q, e.target.value as QuestionType)}
                          disabled={disabled}
                          className="rounded-full border border-border/60 bg-surface/60 px-3 py-1.5 text-xs font-medium text-textMain focus:outline-none focus:ring-2 focus:ring-accent/60"
                        >
                          {typeOptions.map((o) => (
                            <option key={o.value} value={o.value}>
                              {o.label}
                            </option>
                          ))}
                        </select>
                        {onRegenerate && !q.id.startsWith('new_') && (
                          <IconButton
                            label={t('editor.regenerate', { n: idx + 1 })}
                            onClick={() => onRegenerate(q.id)}
                            disabled={disabled || regeneratingIds?.has(q.id)}
                          >
                            <RefreshCw size={16} className={cn(regeneratingIds?.has(q.id) && 'animate-spin')} />
                          </IconButton>
                        )}
                        <IconButton label={t('editor.moveUp')} onClick={() => move(idx, -1)} disabled={disabled || idx === 0}>
                          <ArrowUp size={16} />
                        </IconButton>
                        <IconButton label={t('editor.moveDown')} onClick={() => move(idx, 1)} disabled={disabled || idx === count - 1}>
                          <ArrowDown size={16} />
                        </IconButton>
                        <IconButton
                          label={t('editor.removeQuestion')}
                          onClick={() => update((qs) => qs.filter((x) => x._key !== q._key))}
                          disabled={disabled}
                          danger
                        >
                          <Trash2 size={16} />
                        </IconButton>
                      </div>
                    </div>

                    {regeneratingIds?.has(q.id) && (
                      <p role="status" className="mb-2 text-xs text-muted">
                        {t('editor.regenerating')}
                      </p>
                    )}

                    <label htmlFor={`${q._key}-text`} className="sr-only">
                      {t('editor.questionText')}
                    </label>
                    <textarea
                      id={`${q._key}-text`}
                      value={q.text}
                      onChange={(e) => patchQuestion(q._key, { text: e.target.value })}
                      rows={2}
                      placeholder={t('editor.questionText')}
                      disabled={disabled}
                      className="field mb-3 resize-y py-2 text-sm"
                    />

                    {q.type === 'open' ? (
                      <div>
                        <label htmlFor={`${q._key}-key`} className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted">
                          {t('editor.answerKey')}
                        </label>
                        <textarea
                          id={`${q._key}-key`}
                          value={q.answers[0]?.text ?? ''}
                          onChange={(e) => patchQuestion(q._key, { answers: [{ text: e.target.value, is_correct: true }] })}
                          rows={3}
                          disabled={disabled}
                          className="field resize-y py-2 text-sm"
                        />
                      </div>
                    ) : (
                      <fieldset>
                        <legend className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">{t('editor.answers')}</legend>
                        <div className="flex flex-col gap-2">
                          {q.answers.map((a, i) => (
                            <div
                              key={i}
                              className={cn(
                                'flex items-center gap-2 rounded-lg border px-2 py-1',
                                a.is_correct ? 'border-success/60 bg-success/10' : 'border-border/40',
                              )}
                            >
                              <input
                                type="radio"
                                name={`${q._key}-correct`}
                                checked={a.is_correct}
                                onChange={() => markCorrect(q, i)}
                                aria-label={t('editor.markCorrect', { n: i + 1 })}
                                disabled={disabled}
                                className="h-4 w-4 shrink-0 accent-[rgb(var(--c-success))]"
                              />
                              <input
                                value={a.text}
                                onChange={(e) => setAnswer(q, i, { text: e.target.value })}
                                aria-label={t('editor.answer', { n: i + 1 })}
                                disabled={disabled || q.type === 'tf'}
                                className="min-w-0 flex-1 bg-transparent py-1.5 text-sm text-textMain placeholder:text-muted/70 focus:outline-none"
                                placeholder={t('editor.answer', { n: i + 1 })}
                              />
                              {a.is_correct && (
                                <span className="flex items-center gap-1 text-xs font-semibold text-success">
                                  <CheckCircle2 size={14} aria-hidden="true" /> {t('editor.correct')}
                                </span>
                              )}
                              {q.type === 'mcq' && q.answers.length > 2 && (
                                <IconButton label={t('editor.removeAnswer', { n: i + 1 })} onClick={() => removeAnswer(q, i)} disabled={disabled} danger small>
                                  <X size={14} />
                                </IconButton>
                              )}
                            </div>
                          ))}
                        </div>
                        {q.type === 'mcq' && q.answers.length < MAX_ANSWERS && (
                          <button
                            type="button"
                            onClick={() => patchQuestion(q._key, { answers: [...q.answers, { text: '', is_correct: false }] })}
                            disabled={disabled}
                            className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline disabled:opacity-50"
                          >
                            <Plus size={14} aria-hidden="true" /> {t('editor.addAnswer')}
                          </button>
                        )}
                      </fieldset>
                    )}

                    {q.citations.length > 0 && <Citations citations={q.citations} fileNames={fileNames} />}
                  </>
                )}
              </SortableQuestion>
            ))}
          </ol>
        </SortableContext>
      </DndContext>

      <button
        type="button"
        onClick={addQuestion}
        disabled={disabled}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-border/70 py-3 text-sm font-medium text-muted transition-colors hover:border-accent hover:text-accent disabled:opacity-50"
      >
        <Plus size={16} aria-hidden="true" /> {t('editor.addQuestion')}
      </button>

      {errors.length > 0 && (
        <div ref={errorRef} tabIndex={-1} role="alert" className="mt-4 rounded-xl border border-danger/40 bg-danger/10 p-3 text-sm text-danger focus:outline-none">
          <ul className="list-disc space-y-1 pl-5">
            {errors.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        {canSave ? (
          <label className="flex max-w-md cursor-pointer items-start gap-2 text-xs text-muted">
            <input
              type="checkbox"
              checked={save}
              onChange={(e) => setSave(e.target.checked)}
              disabled={disabled}
              className="mt-0.5 h-4 w-4 shrink-0 accent-[rgb(var(--c-primary))]"
            />
            <span>
              <span className="block text-sm font-medium text-textMain">{t('editor.save.label')}</span>
              {t('editor.save.hint')}
            </span>
          </label>
        ) : (
          <span />
        )}
        <div className="flex flex-wrap items-center gap-2">
          {actions}
          <Button size="sm" onClick={() => void handleSubmit()} disabled={disabled} className="shrink-0">
            {submitLabel ?? t('editor.approve')}
          </Button>
        </div>
      </div>
    </div>
  );
});

export default TestEditor;

function SortableQuestion({ id, disabled, children }: { id: string; disabled?: boolean; children: (handle: React.ReactNode) => React.ReactNode }) {
  const { t } = useTranslation();
  const { attributes, listeners, setNodeRef, setActivatorNodeRef, transform, transition, isDragging } = useSortable({ id, disabled });
  const handle = (
    <button
      type="button"
      ref={setActivatorNodeRef}
      {...attributes}
      {...listeners}
      aria-label={t('editor.dnd.handle')}
      title={t('editor.dnd.handle')}
      className="flex h-8 w-6 cursor-grab touch-none items-center justify-center rounded text-muted hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent active:cursor-grabbing disabled:cursor-not-allowed disabled:opacity-30"
    >
      <GripVertical size={16} aria-hidden="true" />
    </button>
  );
  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn('rounded-xl border border-border/40 bg-background/60 p-4', isDragging && 'relative z-10 shadow-2xl ring-2 ring-accent/60')}
    >
      {children(handle)}
    </li>
  );
}

function Citations({ citations, fileNames }: { citations: Citation[]; fileNames?: Record<string, string> }) {
  const { t } = useTranslation();
  return (
    <details className="mt-3 rounded-lg border border-border/30 bg-surface/40 px-3 py-2 text-xs text-muted">
      <summary className="flex cursor-pointer list-none items-center gap-1.5 font-medium text-textMain/90 [&::-webkit-details-marker]:hidden">
        <BookOpen size={13} aria-hidden="true" /> {t('editor.sources', { count: citations.length })}
      </summary>
      <ul className="mt-2 space-y-2">
        {citations.map((c) => (
          <li key={`${c.file_id}-${c.chunk_id}`}>
            <span className="font-medium text-textMain">{fileNames?.[c.file_id] ?? c.filename ?? t('editor.unknownFile')}</span>
            {c.page ? <span> · {t('editor.page', { page: c.page })}</span> : null}
            {c.snippet && <q className="mt-0.5 block italic">{c.snippet}</q>}
          </li>
        ))}
      </ul>
    </details>
  );
}

function IconButton({
  label,
  children,
  danger,
  small,
  ...props
}: { label: string; children: React.ReactNode; danger?: boolean; small?: boolean } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={cn(
        'flex items-center justify-center rounded-full text-muted transition-colors disabled:opacity-30',
        small ? 'h-7 w-7' : 'h-8 w-8',
        danger ? 'hover:bg-danger/10 hover:text-danger' : 'hover:bg-surface hover:text-accent',
      )}
      {...props}
    >
      {children}
    </button>
  );
}
