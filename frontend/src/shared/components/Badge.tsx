import React from 'react';
import { cn } from '../../lib/utils';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: 'default' | 'secondary' | 'outline' | 'destructive' | 'success';
}

export function Badge({ className, variant = 'default', children, ...props }: BadgeProps) {
    const variants = {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        outline: "border border-border text-foreground",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        success: "bg-emerald-500/15 text-emerald-500 border border-emerald-500/20",
    };

    return (
        <span
            className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2", variants[variant], className)}
            {...props}
        >
            {children}
        </span>
    );
}
