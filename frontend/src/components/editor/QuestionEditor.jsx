import React, { useMemo, useRef, useState } from 'react';
import { ArrowDown, ArrowUp, CheckCircle2, CheckSquare, Plus, Trash2, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Button from '../ui/Button';
import { cn } from '../../utils/cn';

const TYPES = ['mcq', 'tf', 'open'];
const MAX_ANSWERS = 6;
let uid = 0;
const nextId = () => `q${Date.now().toString(36)}${(uid += 1)}`;

const toDraft = (data) => ({
  ...data,
  title: data?.title ?? '',
  questions: (data?.questions ?? []).map((q) => ({
    ...q,
    _id: nextId(),
    type: TYPES.includes(q.type) ? q.type : 'mcq',
    text: q.text ?? '',
    answers: (q.answers ?? []).map((a) => ({ text: a.text ?? '', is_correct: Boolean(a.is_correct) })),
  })),
});

const fromDraft = (draft) => ({
  ...draft,
  title: draft.title.trim(),
  questions: draft.questions.map(({ _id, ...q }) => ({
    ...q,
    text: q.text.trim(),
    answers: q.answers.map((a) => ({ text: a.text.trim(), is_correct: a.is_correct })),
  })),
});

/**
 * Structured editor for a generated exam (human-in-the-loop review, EU AI Act art. 14).
 * Replaces the raw JSON textarea. Emits the same exam JSON shape Skald expects.
 */
export default function QuestionEditor({ initialData, onApprove, disabled, canSave = false }) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState(() => toDraft(initialData));
  const [errors, setErrors] = useState([]);
  const [save, setSave] = useState(false); // opt-in storage (privacy by default)
  const errorRef = useRef(null);

  const update = (fn) => setDraft((d) => ({ ...d, questions: fn(d.questions) }));
  const patchQuestion = (id, patch) => update((qs) => qs.map((q) => (q._id === id ? { ...q, ...patch } : q)));

  const changeType = (q, type) => {
    let answers = q.answers;
    const correct = q.answers.find((a) => a.is_correct)?.text ?? '';
    if (type === 'tf') {
      answers = [
        { text: t('editor.true'), is_correct: true },
        { text: t('editor.false'), is_correct: false },
      ];
    } else if (type === 'open') {
      answers = [{ text: correct, is_correct: true }];
    } else if (type === 'mcq') {
      answers = [...q.answers];
      while (answers.length < 4) answers.push({ text: '', is_correct: false });
      if (!answers.some((a) => a.is_correct)) answers[0] = { ...answers[0], is_correct: true };
    }
    patchQuestion(q._id, { type, answers });
  };

  const setAnswer = (q, idx, patch) =>
    patchQuestion(q._id, { answers: q.answers.map((a, i) => (i === idx ? { ...a, ...patch } : a)) });
  const markCorrect = (q, idx) => patchQuestion(q._id, { answers: q.answers.map((a, i) => ({ ...a, is_correct: i === idx })) });
  const removeAnswer = (q, idx) => {
    const answers = q.answers.filter((_, i) => i !== idx);
    if (!answers.some((a) => a.is_correct) && answers.length) answers[0] = { ...answers[0], is_correct: true };
    patchQuestion(q._id, { answers });
  };

  const move = (idx, dir) =>
    update((qs) => {
      const next = [...qs];
      const [item] = next.splice(idx, 1);
      next.splice(idx + dir, 0, item);
      return next;
    });

  const addQuestion = () =>
    update((qs) => [
      ...qs,
      {
        _id: nextId(),
        type: 'mcq',
        text: '',
        answers: [0, 1, 2, 3].map((i) => ({ text: '', is_correct: i === 0 })),
      },
    ]);

  const validate = () => {
    const errs = [];
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

  const handleApprove = () => {
    const errs = validate();
    setErrors(errs);
    if (errs.length) {
      requestAnimationFrame(() => errorRef.current?.focus());
      return;
    }
    onApprove(fromDraft(draft), { save });
  };

  const count = draft.questions.length;
  const typeOptions = useMemo(() => TYPES.map((type) => ({ value: type, label: t(`editor.types.${type}`) })), [t]);

  return (
    <div className="mt-4 rounded-xl border border-accent/40 bg-surface/80 p-4 shadow-inner md:p-5">
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
        onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
        className="field mb-5 py-2"
        disabled={disabled}
      />

      <ol className="flex flex-col gap-4">
        {draft.questions.map((q, idx) => (
          <li key={q._id} className="rounded-xl border border-border/40 bg-background/60 p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <span className="text-sm font-bold">{t('editor.question', { n: idx + 1 })}</span>
              <div className="flex items-center gap-1">
                <label className="sr-only" htmlFor={`${q._id}-type`}>
                  {t('editor.type')}
                </label>
                <select
                  id={`${q._id}-type`}
                  value={q.type}
                  onChange={(e) => changeType(q, e.target.value)}
                  disabled={disabled}
                  className="rounded-full border border-border/60 bg-surface/60 px-3 py-1.5 text-xs font-medium text-textMain focus:outline-none focus:ring-2 focus:ring-accent/60"
                >
                  {typeOptions.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
                <IconButton label={t('editor.moveUp')} onClick={() => move(idx, -1)} disabled={disabled || idx === 0}>
                  <ArrowUp size={16} />
                </IconButton>
                <IconButton label={t('editor.moveDown')} onClick={() => move(idx, 1)} disabled={disabled || idx === count - 1}>
                  <ArrowDown size={16} />
                </IconButton>
                <IconButton
                  label={t('editor.removeQuestion')}
                  onClick={() => update((qs) => qs.filter((x) => x._id !== q._id))}
                  disabled={disabled}
                  danger
                >
                  <Trash2 size={16} />
                </IconButton>
              </div>
            </div>

            <label htmlFor={`${q._id}-text`} className="sr-only">
              {t('editor.questionText')}
            </label>
            <textarea
              id={`${q._id}-text`}
              value={q.text}
              onChange={(e) => patchQuestion(q._id, { text: e.target.value })}
              rows={2}
              placeholder={t('editor.questionText')}
              disabled={disabled}
              className="field mb-3 resize-y py-2 text-sm"
            />

            {q.type === 'open' ? (
              <div>
                <label htmlFor={`${q._id}-key`} className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted">
                  {t('editor.answerKey')}
                </label>
                <textarea
                  id={`${q._id}-key`}
                  value={q.answers[0]?.text ?? ''}
                  onChange={(e) => patchQuestion(q._id, { answers: [{ text: e.target.value, is_correct: true }] })}
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
                        name={`${q._id}-correct`}
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
                    onClick={() => patchQuestion(q._id, { answers: [...q.answers, { text: '', is_correct: false }] })}
                    disabled={disabled}
                    className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline disabled:opacity-50"
                  >
                    <Plus size={14} aria-hidden="true" /> {t('editor.addAnswer')}
                  </button>
                )}
              </fieldset>
            )}
          </li>
        ))}
      </ol>

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
        <Button size="sm" onClick={handleApprove} disabled={disabled} className="shrink-0">
          {t('editor.approve')}
        </Button>
      </div>
    </div>
  );
}

function IconButton({ label, children, danger, small, ...props }) {
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
