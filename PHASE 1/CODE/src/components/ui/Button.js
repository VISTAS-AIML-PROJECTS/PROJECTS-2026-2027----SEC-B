import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

const Button = React.forwardRef(({ 
  className, 
  variant = "primary", 
  size = "default", 
  children, 
  disabled,
  ...props 
}, ref) => {
  const variants = {
    primary: "bg-primary text-surface hover:bg-primary-container active:scale-[0.99] shadow-sm border border-primary/20",
    secondary: "bg-surface-container-low text-primary hover:bg-surface-container border border-outline-variant/40 active:scale-[0.99]",
    tertiary: "bg-tertiary text-on-tertiary hover:opacity-95 shadow-sm active:scale-[0.99]",
    accent: "bg-primary-container text-on-primary hover:bg-primary shadow-md active:scale-[0.99]",
    outline: "bg-surface border border-primary/40 text-primary hover:bg-surface-container-low",
    ghost: "bg-transparent text-primary hover:bg-surface-container/50",
  };

  const sizes = {
    default: "h-11 px-5 py-2.5 text-sm",
    sm: "h-9 px-3.5 py-1.5 text-xs",
    lg: "h-13 px-6 py-3.5 text-base font-semibold",
    icon: "h-10 w-10 p-0 flex items-center justify-center",
  };

  return (
    <motion.button
      ref={ref}
      disabled={disabled}
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-medium tracking-wide transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 disabled:pointer-events-none disabled:opacity-40 cursor-pointer select-none",
        variants[variant],
        sizes[size],
        className
      )}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      {...props}
    >
      {children}
    </motion.button>
  );
});

Button.displayName = "Button";

export { Button };
export default Button;