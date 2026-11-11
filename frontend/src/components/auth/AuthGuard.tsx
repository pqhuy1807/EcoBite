'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface AuthGuardProps {
    children: React.ReactNode;
    allowedRoles?: string[];
}

export function AuthGuard({ children, allowedRoles }: AuthGuardProps) {
    const router = useRouter();
    const [isAuthorized, setIsAuthorized] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        const rawUser = localStorage.getItem('user');

        if (!token) {
            router.replace('/login');
            return;
        }

        if (allowedRoles && allowedRoles.length > 0 && rawUser) {
            try {
                const user = JSON.parse(rawUser);
                if (user?.role && !allowedRoles.includes(user.role)) {
                    router.replace('/');
                    return;
                }
            } catch {
                router.replace('/login');
                return;
            }
        }

        setIsAuthorized(true);
    }, [router, allowedRoles]);

    if (!isAuthorized) {
        return (
            <div className="flex min-h-screen items-center justify-center p-4 text-sm text-gray-500">
                Đang kiểm tra quyền truy cập...
            </div>
        );
    }

    return <>{children}</>;
}