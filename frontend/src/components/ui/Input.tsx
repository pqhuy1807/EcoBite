// frontend/src/components/ui/Input.tsx
'use client';

import React, { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
    { className, label, error, helperText, id, ...props },
    ref
) {
    return (
        <div className="w-full space-y-1">
            {label && (
                <label
                    htmlFor={id}
                    className="block text-sm font-medium text-gray-700"
                >
                    {label}
                </label>
            )}
            <input
                id={id}
                ref={ref}
                className={cn(
                    'block w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 text-sm text-gray-900 placeholder-gray-400 shadow-sm transition focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600 disabled:bg-gray-100',
                    error && 'border-red-500 focus:border-red-500 focus:ring-red-500',
                    className
                )}
                {...props}
            />
            {error ? (
                <p className="text-xs text-red-600">{error}</p>
            ) : (
                helperText && <p className="text-xs text-gray-500">{helperText}</p>
            )}
        </div>
    );
});