// frontend/src/components/ui/Toast.tsx
'use client';

import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ToastProps {
    message: string;
    type?: 'success' | 'error' | 'info';
    onClose?: () => void;
}

export function Toast({ message, type = 'info', onClose }: ToastProps) {
    const styles = {
        success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
        error: 'border-red-200 bg-red-50 text-red-800',
        info: 'border-blue-200 bg-blue-50 text-blue-800',
    };

    const icons = {
        success: <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />,
        error: <AlertCircle className="h-5 w-5 text-red-600 shrink-0" />,
        info: <Info className="h-5 w-5 text-blue-600 shrink-0" />,
    };

    return (
        <div
            className={cn(
                'flex items-center justify-between gap-3 rounded-xl border p-3.5 text-sm shadow-md',
                styles[type]
            )}
            role="alert"
        >
            <div className="flex items-center gap-2.5">
                {icons[type]}
                <span className="font-medium">{message}</span>
            </div>
            {onClose && (
                <button
                    type="button"
                    onClick={onClose}
                    className="rounded p-1 opacity-70 hover:opacity-100"
                    aria-label="Đóng thông báo"
                >
                    <X className="h-4 w-4" />
                </button>
            )}
        </div>
    );
}