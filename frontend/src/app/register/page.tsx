'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Leaf, Store, UserPlus } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Toast } from '@/components/ui/Toast';
import { extractApiErrorMessage } from '@/lib/api-client';
import { authService } from '@/services/auth.service';
import type { UserRole } from '@/types/api';

export default function RegisterPage() {
    const router = useRouter();
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState<UserRole>('CONSUMER');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setToast(null);
        try {
            await authService.register({
                full_name: fullName.trim(),
                email: email.trim(),
                phone: phone.trim(),
                password,
                role,
            });
            const loginRes = await authService.login({
                email: email.trim(),
                password,
            });
            setToast({
                message: 'Đăng ký thành công! Đang chuyển hướng...',
                type: 'success',
            });
            router.push(loginRes.user.role === 'STORE_PARTNER' ? '/store/onboard' : '/');
        } catch (err) {
            setToast({
                message: extractApiErrorMessage(err, 'Không thể đăng ký tài khoản. Vui lòng thử lại.'),
                type: 'error',
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-md flex-col justify-center px-4 py-10">
            <Card className="p-6 sm:p-8">
                <div className="mb-6 text-center">
                    <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
                        <Leaf className="h-6 w-6" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">Tạo tài khoản EcoBite</h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Tham gia giải cứu thực phẩm dư và tích lũy Green Points
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="mb-1.5 block text-sm font-medium text-gray-700">
                            Vai trò tài khoản
                        </label>
                        <div className="grid grid-cols-2 gap-2.5">
                            <button
                                type="button"
                                onClick={() => setRole('CONSUMER')}
                                className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-medium transition-colors ${
                                    role === 'CONSUMER'
                                        ? 'border-emerald-600 bg-emerald-50 text-emerald-700'
                                        : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                                }`}
                            >
                                <UserPlus className="h-4 w-4" />
                                Người tiêu dùng
                            </button>
                            <button
                                type="button"
                                onClick={() => setRole('STORE_PARTNER')}
                                className={`flex items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-medium transition-colors ${
                                    role === 'STORE_PARTNER'
                                        ? 'border-emerald-600 bg-emerald-50 text-emerald-700'
                                        : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                                }`}
                            >
                                <Store className="h-4 w-4" />
                                Đối tác quán
                            </button>
                        </div>
                    </div>

                    <Input
                        label="Họ và tên"
                        type="text"
                        required
                        minLength={2}
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="Nguyễn Văn An"
                    />
                    <Input
                        label="Email"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="an.nguyen@example.com"
                        autoComplete="email"
                    />
                    <Input
                        label="Số điện thoại"
                        type="tel"
                        required
                        minLength={8}
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="0901234567"
                    />
                    <Input
                        label="Mật khẩu"
                        type="password"
                        required
                        minLength={8}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Tối thiểu 8 ký tự"
                        autoComplete="new-password"
                    />

                    <Button type="submit" className="w-full" size="lg" isLoading={isSubmitting}>
                        Đăng ký tài khoản
                    </Button>
                </form>

                <div className="mt-6 flex items-center justify-between border-t border-gray-100 pt-4 text-sm text-gray-600">
                    <span>Đã có tài khoản?</span>
                    <Link
                        href="/login"
                        className="font-semibold text-emerald-600 hover:text-emerald-700"
                    >
                        Đăng nhập
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
