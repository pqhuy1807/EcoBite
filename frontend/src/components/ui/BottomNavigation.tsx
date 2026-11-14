// frontend/src/components/ui/BottomNavigation.tsx
'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Compass, QrCode, ShoppingBag, Store, User as UserIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { User } from '@/types/api';

function readStoredUser(): User | null {
    if (typeof window === 'undefined') return null;
    try {
        const raw = localStorage.getItem('user');
        return raw ? (JSON.parse(raw) as User) : null;
    } catch {
        return null;
    }
}

export function BottomNavigation() {
    const pathname = usePathname();
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        const syncUser = () => setUser(readStoredUser());
        syncUser();
        window.addEventListener('ecobite-auth-change', syncUser);
        window.addEventListener('storage', syncUser);
        return () => {
            window.removeEventListener('ecobite-auth-change', syncUser);
            window.removeEventListener('storage', syncUser);
        };
    }, []);

    const navItems =
        user?.role === 'STORE_PARTNER'
            ? [
                  { href: '/', label: 'Khám phá', icon: Compass },
                  { href: '/store/verify-qr', label: 'Quét QR', icon: QrCode },
                  { href: '/store/onboard', label: 'Đối tác KYC', icon: Store },
              ]
            : [
                  { href: '/', label: 'Khám phá', icon: Compass },
                  { href: '/orders', label: 'Đơn của tôi', icon: ShoppingBag },
                  { href: '/login', label: user ? user.full_name.split(' ').slice(-1)[0] : 'Tài khoản', icon: UserIcon },
              ];

    return (
        <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-gray-200 bg-white md:hidden">
            <div className="mx-auto flex h-16 max-w-md items-center justify-around px-2">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                'flex flex-col items-center justify-center gap-1 px-3 py-1 text-xs font-medium transition-colors',
                                isActive
                                    ? 'text-emerald-600'
                                    : 'text-gray-500 hover:text-gray-900'
                            )}
                        >
                            <Icon className="h-5 w-5" />
                            <span className="max-w-[80px] truncate">{item.label}</span>
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
}
