import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';

export default function Spinner({ className, label }: { className?: string; label?: string }) {
  const { t } = useTranslation();
  return (
    <div role="status" className={cn('flex items-center justify-center gap-2 text-muted', className)}>
      <Loader2 className="h-6 w-6 animate-spin text-accent" aria-hidden="true" />
      <span className="sr-only">{label ?? t('common.loading')}</span>
    </div>
  );
}

export function PageLoader() {
  return <Spinner className="min-h-[60vh]" />;
}
