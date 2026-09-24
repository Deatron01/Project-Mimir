import { Link, type LinkProps } from 'react-router-dom';
import { buttonClasses, type ButtonSize, type ButtonVariant } from './Button';

type Props = { variant?: ButtonVariant; size?: ButtonSize; className?: string; children: React.ReactNode } & (
  | ({ to: LinkProps['to'] } & Omit<LinkProps, 'to' | 'className'>)
  | ({ href: string } & Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, 'className'>)
);

/** A link styled as a button (never a <button> inside an <a>, which is invalid and confuses screen readers). */
export default function ButtonLink({ variant, size, className, children, ...rest }: Props) {
  const cls = buttonClasses(variant, size, className);
  if ('to' in rest) {
    return (
      <Link className={cls} {...rest}>
        {children}
      </Link>
    );
  }
  return (
    <a className={cls} {...rest}>
      {children}
    </a>
  );
}
