'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Leaf, Lock, Mail, Sparkles, Store, UserCheck } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Toast } from '@/components/ui/Toast';
import { extractApiErrorMessage } from '@/lib/api-client';
import { authService } from '@/services/auth.service';

const DEMO_ACCOUNTS = {
    consumer: {
        email: 'consumer.an@ecobite.vn',
        password: 'Password123!',
        label: 'Consumer Demo (Nguyễn Văn An)',
    },
    storePartner: {
        email: 'merchant.bui@ecobite.vn',
        password: 'Password123!',
        label: 'Store Partner Demo (Cơm Tấm Bụi Q1)',
    },
};

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    const performLogin = async (loginEmail: string, loginPassword: string) => {
        setIsSubmitting(true);
        setToast(null);
        try {
            const res = await authService.login({
                email: loginEmail.trim(),
                password: loginPassword,
            });
            setToast({
                message: `Chào mừng ${res.user.full_name} quay lại EcoBite!`,
                type: 'success',
            });
            const target = res.user.role === 'STORE_PARTNER' ? '/store/verify-qr' : '/';
            router.push(target);
        } catch (err) {
            setToast({
                message: extractApiErrorMessage(err, 'Email hoặc mật khẩu không đúng.'),
                type: 'error',
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await performLogin(email, password);
    };

    const handleDemoLogin = async (type: 'consumer' | 'storePartner') => {
        const account = DEMO_ACCOUNTS[type];
        setEmail(account.email);
        setPassword(account.password);
        await performLogin(account.email, account.password);
    };

    return (
        <div className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-md flex-col justify-center px-4 py-10">
            <Card className="p-6 sm:p-8">
                <div className="mb-6 text-center">
                    <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
                        <Leaf className="h-6 w-6" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">Đăng nhập EcoBite</h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Khám phá món giải cứu gần bạn hoặc quét QR nhận đơn tại quán
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <Input
                        label="Email"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="consumer.an@ecobite.vn"
                        autoComplete="email"
                    />
                    <Input
                        label="Mật khẩu"
                        type="password"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        autoComplete="current-password"
                    />

                    <Button type="submit" className="w-full" size="lg" isLoading={isSubmitting}>
                        <Mail className="h-4 w-4" />
                        Đăng nhập
                    </Button>
                </form>

                <div className="my-6 flex items-center gap-3">
                    <div className="h-px flex-1 bg-gray-200" />
                    <span className="inline-flex items-center gap-1 text-xs font-medium uppercase tracking-wider text-gray-400">
                        <Sparkles className="h-3.5 w-3.5 text-emerald-500" />
                        Đăng nhập nhanh Demo PA3
                    </span>
                    <div className="h-px flex-1 bg-gray-200" />
                </div>

                <div className="space-y-2.5">
                    <Button
                        type="button"
                        variant="outline"
                        className="w-full justify-start border-emerald-200 bg-emerald-50/50 text-emerald-800 hover:bg-emerald-100"
                        disabled={isSubmitting}
                        onClick={() => handleDemoLogin('consumer')}
                    >
                        <UserCheck className="h-4 w-4 text-emerald-600" />
                        <span className="truncate">{DEMO_ACCOUNTS.consumer.label}</span>
                    </Button>
                    <Button
                        type="button"
                        variant="outline"
                        className="w-full justify-start border-amber-200 bg-amber-50/50 text-amber-900 hover:bg-amber-100"
                        disabled={isSubmitting}
                        onClick={() => handleDemoLogin('storePartner')}
                    >
                        <Store className="h-4 w-4 text-amber-600" />
                        <span className="truncate">{DEMO_ACCOUNTS.storePartner.label}</span>
                    </Button>
                </div>

                <div className="mt-6 flex items-center justify-between border-t border-gray-100 pt-4 text-sm text-gray-600">
                    <span>Chưa có tài khoản?</span>
                    <Link
                        href="/register"
                        className="inline-flex items-center gap-1 font-semibold text-emerald-600 hover:text-emerald-700"
                    >
                        <Lock className="h-3.5 w-3.5" />
                        Đăng ký ngay
                    </Link>
                </div>
            </Card>

            {toast && (
                <Toast
                    message={toast.message}
                    type={toast.type}
                    onClose={() => setToast(null)}
                />
            )}
        </div>
    );
}
