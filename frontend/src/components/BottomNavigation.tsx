// frontend/src/components/ui/BottomNavigation.tsx
'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Compass, Store, User } from 'lucide-react';
import { cn } from '@/lib/utils';

export function BottomNavigation() {
    const pathname = usePathname();

    const navItems = [
        { href: '/', label: 'Khám phá', icon: Compass },
        { href: '/store/onboard', label: 'Đối tác KYC', icon: Store },
        { href: '/login', label: 'Tài khoản', icon: User },
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
                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
}