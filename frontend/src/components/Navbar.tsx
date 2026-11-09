// frontend/src/components/ui/Navbar.tsx
'use client';

import React from 'react';
import Link from 'next/link';
import { Leaf, MapPin, Store, User as UserIcon } from 'lucide-react';

export function Navbar() {
    return (
        <header className="sticky top-0 z-40 w-full border-b border-gray-200 bg-white/95 backdrop-blur-xs">
            <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
                <Link href="/" className="flex items-center gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-600 text-white">
                        <Leaf className="h-5 w-5" />
                    </div>
                    <span className="text-xl font-bold tracking-tight text-gray-900">
                        Eco<span className="text-emerald-600">Bite</span>
                    </span>
                </Link>

                <nav className="hidden items-center gap-6 md:flex">
                    <Link
                        href="/"
                        className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-emerald-600"
                    >
                        <MapPin className="h-4 w-4" />
                        Radar Quán Gần Đây
                    </Link>
                    <Link
                        href="/store/onboard"
                        className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-emerald-600"
                    >
                        <Store className="h-4 w-4" />
                        Đăng Ký Cửa Hàng (KYC)
                    </Link>
                </nav>

                <div className="flex items-center gap-3">
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
                </div>
            </div>
        </header>
    );
}