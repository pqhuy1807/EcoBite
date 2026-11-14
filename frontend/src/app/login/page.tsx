'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!email || !password) {
            setError('Vui lòng nhập đầy đủ email và mật khẩu.');
            return;
        }

        setIsLoading(true);
        try {
            const { data } = await apiClient.post('/auth/login', {
                email,
                password,
            });

            if (data?.access_token) {
                localStorage.setItem('access_token', data.access_token);
            }
            if (data?.user) {
                localStorage.setItem('user', JSON.stringify(data.user));
            }

            const userRole = data?.user?.role || 'CONSUMER';
            if (userRole === 'STORE_PARTNER') {
                router.push('/onboard');
            } else {
                router.push('/radar');
            }
        } catch {
            setError('Email hoặc mật khẩu không chính xác. Vui lòng kiểm tra lại.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-[#EEF5F0] px-4 py-8">
            <div className="grid w-full max-w-4xl grid-cols-1 overflow-hidden rounded-3xl bg-white p-6 shadow-lg sm:p-10 md:grid-cols-12 md:p-14">
                {/* Cột trái: Thương hiệu EcoBite (Đồng bộ kích thước Desktop & Mobile) */}
                <div className="flex flex-col justify-center pb-8 text-center md:col-span-5 md:pb-0 md:pr-8 md:text-left">
                    <div className="mb-2 inline-flex items-center justify-center gap-2 md:justify-start">
                        <span className="text-2xl">🍃</span>
                        <h1 className="text-3xl font-bold tracking-tight text-[#1E703D]">
                            Ecobite platform
                        </h1>
                    </div>
                    <p className="text-sm text-gray-600">Your Food Rescue Friend</p>
                </div>

                {/* Cột phải: Biểu mẫu Đăng nhập */}
                <div className="md:col-span-7">
                    <div className="mb-6">
                        <h2 className="text-2xl font-bold text-gray-900">
                            Đăng nhập tài khoản
                        </h2>
                        <p className="mt-1 text-sm text-gray-600">
                            Sign in to your Ecobite account.
                        </p>
                    </div>

                    {/* Khung báo lỗi xác thực (Alternative Flow từ Figma) */}
                    {error && (
                        <div className="mb-5 flex items-start gap-2.5 rounded-xl border border-red-300 bg-[#FEF2F2] p-3.5 text-xs text-red-600">
                            <span className="mt-0.5 text-sm">⚠️</span>
                            <span>{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="mb-1.5 block text-sm font-medium text-gray-800">
                                Email Address
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="Peter@example.com"
                                className="w-full rounded-xl border border-transparent bg-[#F1F6F2] px-4 py-3 text-sm text-gray-900 placeholder-gray-400 outline-none transition focus:border-[#1E703D] focus:bg-white"
                            />
                        </div>

                        <div>
                            <label className="mb-1.5 block text-sm font-medium text-gray-800">
                                Password
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter your password"
                                className={`w-full rounded-xl border px-4 py-3 text-sm text-gray-900 placeholder-gray-400 outline-none transition ${error
                                        ? 'border-red-500 bg-white focus:border-red-600'
                                        : 'border-transparent bg-[#F1F6F2] focus:border-[#1E703D] focus:bg-white'
                                    }`}
                            />
                            {error && (
                                <p className="mt-1.5 text-xs text-red-500">
                                    Mật khẩu không khớp với tài khoản này
                                </p>
                            )}
                        </div>

                        <div className="flex justify-end">
                            <button
                                type="button"
                                className="text-xs font-semibold text-[#1E703D] hover:underline"
                            >
                                Forgot password?
                            </button>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full rounded-xl bg-[#1E703D] py-3.5 text-sm font-semibold text-white transition hover:bg-[#16562E] disabled:opacity-60"
                        >
                            {isLoading ? 'Signing in...' : 'Sign in'}
                        </button>
                    </form>

                    <p className="mt-6 text-center text-xs text-gray-600">
                        Don&apos;t have an account?{' '}
                        <Link
                            href="/register"
                            className="font-semibold text-[#1E703D] hover:underline"
                        >
                            Sign up
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}