import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

const Button = React.forwardRef(({
  className,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  children,
  ...props
}, ref) => {
  
  const baseStyles = "inline-flex items-center justify-center rounded-full font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:pointer-events-none disabled:opacity-50";
  
  const variants = {
    primary: "bg-primary text-textMain hover:bg-accent hover:text-background",
    secondary: "bg-surface text-textMain hover:bg-border",
    outline: "border border-border bg-transparent hover:bg-surface text-textMain",
    ghost: "bg-transparent hover:bg-surface/50 text-accent",
  };

  const sizes = {
    sm: "h-9 px-4 text-sm",
    md: "h-11 px-8 text-base",
    lg: "h-14 px-10 text-lg",
  };

  return (
    <motion.button
      ref={ref}
      whileHover={{ scale: disabled || isLoading ? 1 : 1.02 }}
      whileTap={{ scale: disabled || isLoading ? 1 : 0.98 }}
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      disabled={disabled || isLoading}
      aria-disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="mr-2 h-5 w-5 animate-spin" aria-hidden="true" />}
      {children}
    </motion.button>
  );
});

Button.displayName = "Button";

export default Button;