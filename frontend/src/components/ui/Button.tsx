import React from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'icon' | 'sm' | 'md' | 'lg';
export interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  children?: React.ReactNode;
}

const baseStyles =
  'inline-flex items-center justify-center gap-2 rounded-full font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50';

const variants: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-onPrimary hover:bg-primary/85 shadow-sm',
  secondary: 'bg-surface text-textMain hover:bg-surface/70 border border-border/40',
  outline: 'border border-border/70 bg-transparent hover:bg-surface/60 text-textMain',
  ghost: 'bg-transparent hover:bg-surface/60 text-accent',
  danger: 'bg-transparent border border-danger/50 text-danger hover:bg-danger/10',
};

const sizes: Record<ButtonSize, string> = {
  icon: 'h-9 w-9 p-0',
  sm: 'h-9 px-4 text-sm',
  md: 'h-11 px-8 text-base',
  lg: 'h-14 px-10 text-lg',
};

/** Class list shared by <Button> and <ButtonLink>, so a link can look like a button without nesting one. */
export const buttonClasses = (variant: ButtonVariant = 'primary', size: ButtonSize = 'md', className?: string) =>
  cn(baseStyles, variants[variant], sizes[size], className);

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading = false, disabled, children, ...props }, ref) => {
    const inactive = disabled || isLoading;
    return (
      <motion.button
        ref={ref}
        whileHover={{ scale: inactive ? 1 : 1.02 }}
        whileTap={{ scale: inactive ? 1 : 0.98 }}
        className={buttonClasses(variant, size, className)}
        disabled={inactive}
        aria-busy={isLoading || undefined}
        {...props}
      >
        {isLoading && <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />}
        {children}
      </motion.button>
    );
  },
);

Button.displayName = 'Button';

export default Button;
