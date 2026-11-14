'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';

type AccountRole = 'customer' | 'store-partner';
type PartnerSubRole = 'Manager' | 'Member';

export default function RegisterPage() {
    const router = useRouter();
    const [role, setRole] = useState<AccountRole>('customer');
    const [subRole, setSubRole] = useState<PartnerSubRole>('Manager');

    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [workspaceId, setWorkspaceId] = useState('');
    const [workspacePin, setWorkspacePin] = useState('');

    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!username || !email) {
            setError('Vui lòng nhập đầy đủ Username và Email.');
            return;
        }

        if (role === 'store-partner' && subRole === 'Member') {
            if (!workspaceId || !workspacePin) {
                setError('Vui lòng nhập Workspace ID và mã PIN.');
                return;
            }
        } else if (password.length < 9) {
            setError('Mật khẩu cần dài ít nhất 9 ký tự.');
            return;
        }

        setIsLoading(true);
        try {
            const backendRole = role === 'customer' ? 'CONSUMER' : 'STORE_PARTNER';
            await apiClient.post('/auth/register', {
                full_name: username,
                email,
                password:
                    role === 'store-partner' && subRole === 'Member'
                        ? workspacePin
                        : password,
                role: backendRole,
                workspace_id:
                    role === 'store-partner' && subRole === 'Member'
                        ? workspaceId
                        : undefined,
            });

            if (backendRole === 'STORE_PARTNER') {
                router.push('/onboard');
            } else {
                router.push('/login');
            }
        } catch {
            setError('Đăng ký không thành công. Email có thể đã tồn tại.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-[#EEF5F0] px-4 py-8">
            <div className="grid w-full max-w-4xl grid-cols-1 overflow-hidden rounded-3xl bg-white p-6 shadow-lg sm:p-10 md:grid-cols-12 md:p-14">
                {/* Cột trái: Thương hiệu EcoBite */}
                <div className="flex flex-col justify-center pb-8 text-center md:col-span-5 md:pb-0 md:pr-8 md:text-left">
                    <h1 className="text-3xl font-bold tracking-tight text-[#1E703D]">
                        Ecobite platform
                    </h1>
                    <p className="mt-2 text-sm text-gray-600">Your Food Rescue Friend</p>
                </div>

                {/* Cột phải: Biểu mẫu Đăng ký */}
                <div className="md:col-span-7">
                    {/* Nút chọn vai trò: customer | store-partner */}
                    <div className="mb-5 grid grid-cols-2 gap-3">
                        <button
                            type="button"
                            onClick={() => setRole('customer')}
                            className={`rounded-lg py-2.5 text-xs font-medium transition ${role === 'customer'
                                    ? 'bg-[#1E703D] text-white shadow-sm'
                                    : 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                                }`}
                        >
                            customer
                        </button>
                        <button
                            type="button"
                            onClick={() => setRole('store-partner')}
                            className={`rounded-lg py-2.5 text-xs font-medium transition ${role === 'store-partner'
                                    ? 'bg-[#1E703D] text-white shadow-sm'
                                    : 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                                }`}
                        >
                            store-partner
                        </button>
                    </div>

                    {/* Thanh chọn phụ khi là store-partner: Manager | Member */}
                    {role === 'store-partner' && (
                        <div className="mb-5 flex items-center gap-4">
                            <span className="text-sm font-medium text-gray-800">
                                You are?
                            </span>
                            <div className="grid flex-1 grid-cols-2 rounded-full bg-[#F1F6F2] p-1">
                                <button
                                    type="button"
                                    onClick={() => setSubRole('Manager')}
                                    className={`rounded-full py-1.5 text-xs font-medium transition ${subRole === 'Manager'
                                            ? 'bg-[#1E703D] text-white shadow-sm'
                                            : 'text-gray-700 hover:text-gray-900'
                                        }`}
                                >
                                    Manager
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setSubRole('Member')}
                                    className={`rounded-full py-1.5 text-xs font-medium transition ${subRole === 'Member'
                                            ? 'bg-[#1E703D] text-white shadow-sm'
                                            : 'text-gray-700 hover:text-gray-900'
                                        }`}
                                >
                                    Member
                                </button>
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="mb-4 rounded-xl border border-red-300 bg-[#FEF2F2] p-3 text-xs text-red-600">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="mb-1.5 block text-sm font-medium text-gray-800">
                                Username
                            </label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="How should we call you?"
                                className="w-full rounded-xl border border-transparent bg-[#F1F6F2] px-4 py-3 text-sm text-gray-900 placeholder-gray-400 outline-none transition focus:border-[#1E703D] focus:bg-white"
                            />
                        </div>

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

                        {/* Nhánh Member của store-partner */}
                        {role === 'store-partner' && subRole === 'Member' ? (
                            <>
                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-gray-800">
                                        Workspace ID
                                    </label>
                                    <input
                                        type="text"
                                        value={workspaceId}
                                        onChange={(e) => setWorkspaceId(e.target.value)}
                                        placeholder="Enter the ID given by your Manager"
                                        className="w-full rounded-xl border border-transparent bg-[#F1F6F2] px-4 py-3 text-sm text-gray-900 placeholder-gray-400 outline-none transition focus:border-[#1E703D] focus:bg-white"
                                    />
                                </div>
                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-gray-800">
                                        Workspace Password
                                    </label>
                                    <input
                                        type="password"
                                        value={workspacePin}
                                        onChange={(e) => setWorkspacePin(e.target.value)}
                                        placeholder="PIN code for workspace"
                                        className="w-full rounded-xl border border-transparent bg-[#F1F6F2] px-4 py-3 text-sm text-gray-900 placeholder-gray-400 outline-none transition focus:border-[#1E703D] focus:bg-white"
                                    />
                                </div>
                            </>
                        ) : (
                            /* Nhánh Customer hoặc Store Manager */
                            <div>
                                <label className="mb-1.5 block text-sm font-medium text-gray-800">
                                    Password
                                </label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="The password should be longer than 9 characters"
                                    className="w-full rounded-xl border border-transparent bg-[#F1F6F2] px-4 py-3 text-sm text-gray-900 placeholder-gray-400 outline-none transition focus:border-[#1E703D] focus:bg-white"
                                />
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="mt-2 w-full rounded-xl bg-[#1E703D] py-3.5 text-sm font-semibold text-white transition hover:bg-[#16562E] disabled:opacity-60"
                        >
                            {isLoading ? 'Creating account...' : 'Sign Up'}
                        </button>
                    </form>

                    <p className="mt-5 text-center text-xs text-gray-600">
                        Already have an account?{' '}
                        <Link
                            href="/login"
                            className="font-semibold text-[#1E703D] hover:underline"
                        >
                            Sign in
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}