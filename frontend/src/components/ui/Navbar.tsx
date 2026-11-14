// frontend/src/components/ui/Navbar.tsx
'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
    Leaf,
    LogOut,
    MapPin,
    QrCode,
    ShoppingBag,
    Store,
    User as UserIcon,
} from 'lucide-react';
import { authService } from '@/services/auth.service';
import type { User } from '@/types/api';
import { cn } from '@/lib/utils';

function readStoredUser(): User | null {
    if (typeof window === 'undefined') return null;
    try {
        const raw = localStorage.getItem('user');
        return raw ? (JSON.parse(raw) as User) : null;
    } catch {
        return null;
    }
}

export function Navbar() {
    const pathname = usePathname();
    const router = useRouter();
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

    const handleLogout = () => {
        authService.logout();
        setUser(null);
        router.push('/login');
    };

    const roleLabel =
        user?.role === 'CONSUMER'
            ? 'Người giải cứu'
            : user?.role === 'STORE_PARTNER'
              ? 'Đối tác quán'
              : user?.role === 'ADMIN'
                ? 'Quản trị'
                : '';

    return (
        <header className="sticky top-0 z-40 w-full border-b border-gray-200 bg-white/95 backdrop-blur-sm">
            <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
                <Link href="/" className="flex items-center gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm">
                        <Leaf className="h-5 w-5" />
                    </div>
                    <span className="text-xl font-bold tracking-tight text-gray-900">
                        Eco<span className="text-emerald-600">Bite</span>
                    </span>
                </Link>

                <nav className="hidden items-center gap-5 md:flex">
                    <Link
                        href="/"
                        className={cn(
                            'flex items-center gap-1.5 text-sm font-medium transition-colors',
                            pathname === '/'
                                ? 'text-emerald-700'
                                : 'text-gray-600 hover:text-emerald-600'
                        )}
                    >
                        <MapPin className="h-4 w-4" />
                        Radar Quán Gần Đây
                    </Link>

                    {(!user || user.role === 'CONSUMER' || user.role === 'ADMIN') && (
                        <Link
                            href="/orders"
                            className={cn(
                                'flex items-center gap-1.5 text-sm font-medium transition-colors',
                                pathname === '/orders'
                                    ? 'text-emerald-700'
                                    : 'text-gray-600 hover:text-emerald-600'
                            )}
                        >
                            <ShoppingBag className="h-4 w-4" />
                            Đơn của tôi
                        </Link>
                    )}

                    {(!user || user.role === 'STORE_PARTNER' || user.role === 'ADMIN') && (
                        <Link
                            href="/store/verify-qr"
                            className={cn(
                                'flex items-center gap-1.5 text-sm font-medium transition-colors',
                                pathname === '/store/verify-qr'
                                    ? 'text-emerald-700'
                                    : 'text-gray-600 hover:text-emerald-600'
                            )}
                        >
                            <QrCode className="h-4 w-4" />
                            Quét QR Quán
                        </Link>
                    )}

                    {(!user || user.role === 'STORE_PARTNER' || user.role === 'ADMIN') && (
                        <Link
                            href="/store/onboard"
                            className={cn(
                                'flex items-center gap-1.5 text-sm font-medium transition-colors',
                                pathname === '/store/onboard'
                                    ? 'text-emerald-700'
                                    : 'text-gray-600 hover:text-emerald-600'
                            )}
                        >
                            <Store className="h-4 w-4" />
                            Đăng Ký Cửa Hàng (KYC)
                        </Link>
                    )}
                </nav>

                <div className="flex items-center gap-2.5">
                    {user ? (
                        <>
                            <div className="hidden items-center gap-2 rounded-lg border border-emerald-100 bg-emerald-50/70 px-3 py-1.5 sm:flex">
                                <UserIcon className="h-4 w-4 text-emerald-700" />
                                <div className="leading-tight">
                                    <p className="max-w-[140px] truncate text-xs font-semibold text-gray-900">
                                        {user.full_name}
                                    </p>
                                    <p className="text-[11px] font-medium text-emerald-700">
                                        {roleLabel}
                                    </p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={handleLogout}
                                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
                            >
                                <LogOut className="h-4 w-4" />
                                <span className="hidden sm:inline">Đăng xuất</span>
                            </button>
                        </>
                    ) : (
                        <>
                            <Link
                                href="/login"
                                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3.5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                            >
                                <UserIcon className="h-4 w-4" />
                                Đăng nhập
                            </Link>
                            <Link
                                href="/register"
                                className="rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                            >
                                Đăng ký
                            </Link>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}
