import React from 'react';
import { cn } from '../../utils/cn';

export function Badge({ 
  children, 
  variant = 'default', 
  size = 'default',
  icon,
  className,
  ...props 
}) {
  const variants = {
    default: "bg-surface-container text-primary border-outline-variant/40",
    forest: "bg-primary text-surface border-transparent",
    sage: "bg-secondary-container/60 text-on-secondary-container border-secondary/20",
    terracotta: "bg-tertiary-fixed text-on-tertiary-fixed border-tertiary/20",
    outline: "bg-transparent text-primary border-outline-variant/60",
    bio: "bg-[#8caa88]/15 text-[#2e4a3a] border-[#8caa88]/30",
  };

  const sizes = {
    default: "px-2.5 py-1 text-[11px]",
    sm: "px-2 py-0.5 text-[10px]",
    lg: "px-3 py-1.5 text-xs",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-label-caps tracking-wider uppercase font-semibold rounded-full border shadow-2xs",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {icon && (
        <span className="material-symbols-outlined text-[13px] leading-none">
          {icon}
        </span>
      )}
      <span>{children}</span>
    </span>
  );
}

export default Badge;
