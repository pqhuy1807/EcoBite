'use client';

import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { CheckCircle2, MapPin, Store } from 'lucide-react';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Toast } from '@/components/ui/Toast';
import { extractApiErrorMessage } from '@/lib/api-client';
import { storeService } from '@/services/store.service';
import type { StoreOnboardResponse } from '@/types/api';

const PARTNER_ROLES = ['STORE_PARTNER', 'ADMIN'];

export default function StoreOnboardPage() {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [address, setAddress] = useState('');
    const [latitude, setLatitude] = useState('10.7769');
    const [longitude, setLongitude] = useState('106.7009');
    const [phone, setPhone] = useState('');
    const [kycLicenseUrl, setKycLicenseUrl] = useState('https://ecobite.vn/kyc/atvstp-demo.pdf');
    const [result, setResult] = useState<StoreOnboardResponse | null>(null);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    const onboardMutation = useMutation({
        mutationFn: storeService.onboardStore,
        onSuccess: (res) => {
            setResult(res);
            setToast({
                message: `Đã gửi hồ sơ KYC cho cửa hàng "${res.name}"!`,
                type: 'success',
            });
        },
        onError: (err) => {
            setToast({
                message: extractApiErrorMessage(err, 'Không thể gửi đăng ký cửa hàng.'),
                type: 'error',
            });
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onboardMutation.mutate({
            name: name.trim(),
            description: description.trim(),
            address: address.trim(),
            latitude: Number(latitude),
            longitude: Number(longitude),
            phone: phone.trim(),
            kyc_license_url: kycLicenseUrl.trim(),
        });
    };

    const fillCurrentGps = () => {
        if (!navigator.geolocation) return;
        navigator.geolocation.getCurrentPosition((pos) => {
            setLatitude(pos.coords.latitude.toFixed(6));
            setLongitude(pos.coords.longitude.toFixed(6));
        });
    };

    return (
        <AuthGuard allowedRoles={PARTNER_ROLES}>
            <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
                <Card className="p-6 sm:p-8">
                    <div className="mb-6">
                        <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                            <Store className="h-3.5 w-3.5" />
                            Đăng ký Đối tác EcoBite (KYC & GPS)
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            Đăng ký Cửa hàng & Chứng nhận ATVSTP
                        </h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Cửa hàng sau khi Admin phê duyệt sẽ xuất hiện trên bản đồ Radar cho khách hàng gần bạn.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <Input
                            label="Tên cửa hàng"
                            required
                            minLength={2}
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Tiệm Bánh Mì & Cơm Trưa Sài Gòn"
                        />

                        <Input
                            label="Địa chỉ thực tế"
                            required
                            minLength={5}
                            value={address}
                            onChange={(e) => setAddress(e.target.value)}
                            placeholder="123 Lê Lợi, Phường Bến Thành, Quận 1, TP.HCM"
                        />

                        <div>
                            <label className="mb-1.5 block text-sm font-medium text-gray-700">
                                Mô tả giới thiệu cửa hàng
                            </label>
                            <textarea
                                rows={2}
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Chuyên phục vụ cơm văn phòng, bánh mì tươi mỗi ngày..."
                                className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                            />
                        </div>

                        <div className="grid gap-4 sm:grid-cols-2">
                            <Input
                                label="Vĩ độ (Latitude)"
                                type="number"
                                step="any"
                                required
                                value={latitude}
                                onChange={(e) => setLatitude(e.target.value)}
                            />
                            <Input
                                label="Kinh độ (Longitude)"
                                type="number"
                                step="any"
                                required
                                value={longitude}
                                onChange={(e) => setLongitude(e.target.value)}
                            />
                        </div>

                        <div className="flex justify-end">
                            <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={fillCurrentGps}
                            >
                                <MapPin className="h-3.5 w-3.5 text-emerald-600" />
                                Lấy tọa độ GPS hiện tại
                            </Button>
                        </div>

                        <div className="grid gap-4 sm:grid-cols-2">
                            <Input
                                label="Số điện thoại liên hệ"
                                value={phone}
                                onChange={(e) => setPhone(e.target.value)}
                                placeholder="0909123456"
                            />
                            <Input
                                label="Link chứng nhận ATVSTP (KYC)"
                                value={kycLicenseUrl}
                                onChange={(e) => setKycLicenseUrl(e.target.value)}
                                placeholder="https://..."
                            />
                        </div>

                        <Button
                            type="submit"
                            className="w-full"
                            size="lg"
                            isLoading={onboardMutation.isPending}
                        >
                            Gửi hồ sơ đăng ký cửa hàng
                        </Button>
                    </form>

                    {result && (
                        <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                            <div className="flex items-start gap-2.5">
                                <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-600" />
                                <div className="space-y-1 text-sm">
                                    <div className="flex items-center gap-2">
                                        <p className="font-bold text-emerald-900">{result.name}</p>
                                        <Badge variant="warning">{result.kyc_status}</Badge>
                                    </div>
                                    <p className="text-xs text-emerald-800">
                                        Store ID: <span className="font-mono">{result.id}</span>
                                    </p>
                                    {result.message && (
                                        <p className="text-xs text-emerald-700">{result.message}</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </Card>

                {toast && (
                    <Toast
                        message={toast.message}
                        type={toast.type}
                        onClose={() => setToast(null)}
                    />
                )}
            </div>
        </AuthGuard>
    );
}
