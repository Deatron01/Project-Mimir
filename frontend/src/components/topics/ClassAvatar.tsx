import { cn } from '../../utils/cn';

/** Up to two initials: "Biology 9 – Photosynthesis" → "B9", "Math" → "M". */
export function initials(name: string): string {
  // Only letters and digits count: "Fotoszintézis (demo)" → "FD", not "F(".
  const words = name.match(/[\p{L}\p{N}]+/gu) ?? [];
  const [a = '', b = ''] = words;
  if (!a) return '?';
  return ([...a][0] + ([...b][0] ?? '')).toUpperCase();
}

const SIZES = { sm: 'h-8 w-8 rounded-lg text-xs', md: 'h-11 w-11 rounded-xl text-sm', lg: 'h-14 w-14 rounded-2xl text-lg' };

/** A class's badge: its initials on the palette's primary colour. Decorative; the name is always shown next to it. */
export default function ClassAvatar({ name, size = 'md', className }: { name: string; size?: keyof typeof SIZES; className?: string }) {
  return (
    <span aria-hidden="true" className={cn('flex shrink-0 items-center justify-center bg-primary font-extrabold text-onPrimary shadow-sm', SIZES[size], className)}>
      {initials(name)}
    </span>
  );
}
