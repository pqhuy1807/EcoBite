'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    AlertCircle,
    Camera,
    CameraOff,
    CheckCircle2,
    ClipboardList,
    Clock,
    Leaf,
    QrCode,
    RefreshCw,
    ShieldCheck,
    Sparkles,
} from 'lucide-react';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Toast } from '@/components/ui/Toast';
import { extractApiErrorMessage } from '@/lib/api-client';
import { formatDateTime, formatVND } from '@/lib/utils';
import { orderService } from '@/services/order.service';
import { storeService } from '@/services/store.service';
import type { OrderStatus, PaymentStatus, QRVerificationResponse } from '@/types/api';

const PARTNER_ROLES = ['STORE_PARTNER', 'ADMIN'];

type StoreOrderTab = 'ALL' | 'PENDING_PICKUP' | 'COMPLETED';

function getOrderStatusBadge(status: OrderStatus): {
    label: string;
    variant: 'success' | 'warning' | 'danger' | 'info' | 'neutral';
} {
    switch (status) {
        case 'CONFIRMED':
            return { label: 'Đã xác nhận', variant: 'info' };
        case 'READY_FOR_PICKUP':
            return { label: 'Chờ khách lấy', variant: 'warning' };
        case 'COMPLETED':
            return { label: 'Đã giao', variant: 'success' };
        case 'CANCELLED':
            return { label: 'Đã hủy', variant: 'danger' };
        case 'EXPIRED':
            return { label: 'Hết hạn', variant: 'neutral' };
        default:
            return { label: status, variant: 'neutral' };
    }
}

function getPaymentBadgeVariant(
    status: PaymentStatus
): 'success' | 'warning' | 'danger' | 'neutral' {
    switch (status) {
        case 'PAID':
            return 'success';
        case 'PENDING':
            return 'warning';
        case 'FAILED':
            return 'danger';
        default:
            return 'neutral';
    }
}

export default function StoreVerifyQrPage() {
    const queryClient = useQueryClient();
    const [qrToken, setQrToken] = useState('');
    const [scannerActive, setScannerActive] = useState(false);
    const [cameraError, setCameraError] = useState<string | null>(null);
    const [verificationResult, setVerificationResult] = useState<QRVerificationResponse | null>(
        null
    );
    const [verificationError, setVerificationError] = useState<string | null>(null);
    const [orderTab, setOrderTab] = useState<StoreOrderTab>('PENDING_PICKUP');
    const [toast, setToast] = useState<{
        message: string;
        type: 'success' | 'error' | 'info';
    } | null>(null);

    const scannerRef = useRef<{ stop: () => Promise<void>; clear: () => void } | null>(null);

    const {
        data: myStore,
        isLoading: storeLoading,
        error: storeError,
    } = useQuery({
        queryKey: ['my-store'],
        queryFn: () => storeService.getMyStore(),
        retry: false,
    });

    const {
        data: storeOrders = [],
        isLoading: ordersLoading,
        isFetching: ordersFetching,
        error: ordersError,
        refetch: refetchOrders,
    } = useQuery({
        queryKey: ['store-orders', myStore?.id],
        queryFn: () => orderService.getStoreOrders(myStore!.id),
        enabled: Boolean(myStore?.id),
    });

    const filteredOrders = useMemo(() => {
        if (orderTab === 'PENDING_PICKUP') {
            return storeOrders.filter(
                (o) => o.status === 'CONFIRMED' || o.status === 'READY_FOR_PICKUP'
            );
        }
        if (orderTab === 'COMPLETED') {
            return storeOrders.filter((o) => o.status === 'COMPLETED');
        }
        return storeOrders;
    }, [storeOrders, orderTab]);

    const pendingCount = useMemo(
        () =>
            storeOrders.filter(
                (o) => o.status === 'CONFIRMED' || o.status === 'READY_FOR_PICKUP'
            ).length,
        [storeOrders]
    );

    const completedCount = useMemo(
        () => storeOrders.filter((o) => o.status === 'COMPLETED').length,
        [storeOrders]
    );

    const verifyMutation = useMutation({
        mutationFn: (token: string) => orderService.verifyOrderQr(token),
        onSuccess: (res) => {
            setVerificationError(null);
            setVerificationResult(res);
            setToast({
                message: `Xác thực thành công đơn ${res.order_code}!`,
                type: 'success',
            });
            void queryClient.invalidateQueries({ queryKey: ['store-orders'] });
        },
        onError: (err) => {
            const msg = extractApiErrorMessage(
                err,
                'Mã QR không hợp lệ, đã được sử dụng hoặc không thuộc cửa hàng của bạn.'
            );
            setVerificationResult(null);
            setVerificationError(msg);
            setToast({ message: msg, type: 'error' });
        },
    });

    const stopCameraScanner = async () => {
        if (scannerRef.current) {
            try {
                await scannerRef.current.stop();
                scannerRef.current.clear();
            } catch {
                // ignore cleanup errors if scanner already stopped
            }
            scannerRef.current = null;
        }
        setScannerActive(false);
    };

    useEffect(() => {
        if (!scannerActive) return;

        let cancelled = false;
        const startScanner = async () => {
            setCameraError(null);
            try {
                const { Html5Qrcode } = await import('html5-qrcode');
                if (cancelled) return;

                const html5Qr = new Html5Qrcode('ecobite-qr-reader');
                scannerRef.current = html5Qr;

                await html5Qr.start(
                    { facingMode: 'environment' },
                    { fps: 10, qrbox: { width: 220, height: 220 } },
                    async (decodedText) => {
                        setQrToken(decodedText);
                        await stopCameraScanner();
                        verifyMutation.mutate(decodedText);
                    },
                    () => {
                        // ignore per-frame decode misses
                    }
                );
            } catch (err) {
                const message =
                    err instanceof Error
                        ? err.message
                        : 'Không thể khởi động camera. Vui lòng dùng ô dán mã QR bên dưới.';
                setCameraError(message);
                setScannerActive(false);
            }
        };

        void startScanner();

        return () => {
            cancelled = true;
            if (scannerRef.current) {
                scannerRef.current
                    .stop()
                    .then(() => scannerRef.current?.clear())
                    .catch(() => undefined);
                scannerRef.current = null;
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [scannerActive]);

    const handleVerifySubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const trimmed = qrToken.trim();
        if (!trimmed) {
            setVerificationError('Vui lòng nhập hoặc quét chuỗi mã QR của khách hàng.');
            return;
        }
        verifyMutation.mutate(trimmed);
    };

    return (
        <AuthGuard allowedRoles={PARTNER_ROLES}>
            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="mb-6">
                    <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                        <ShieldCheck className="h-3.5 w-3.5" />
                        Cổng Đối Tác Cửa Hàng • HMAC-SHA256 Anti-Replay
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">
                        Quét Mã QR & Quản lý Đơn Giao Món
                    </h1>
                    <p className="mt-1 text-sm text-gray-500">
                        {myStore
                            ? `${myStore.name} — Đối soát đơn hàng cần giao, quét QR chống trùng lần 2 và cộng điểm xanh.`
                            : 'Kiểm tra chữ ký HMAC, chống quét trùng lần 2 và cộng điểm xanh cho khách hàng.'}
                    </p>
                </div>

                <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
                    {/* Left Column: Camera + Manual QR Verification */}
                    <div className="space-y-6 lg:col-span-5">
                        {/* Camera Toggle Card */}
                        <Card className="p-5">
                            <div className="flex flex-wrap items-center justify-between gap-3">
                                <div>
                                    <h2 className="text-base font-semibold text-gray-900">
                                        Quét bằng Camera thiết bị
                                    </h2>
                                    <p className="text-xs text-gray-500">
                                        Hướng camera về mã QR trên màn hình khách hàng.
                                    </p>
                                </div>
                                <Button
                                    type="button"
                                    variant={scannerActive ? 'danger' : 'outline'}
                                    size="sm"
                                    onClick={() => {
                                        if (scannerActive) {
                                            void stopCameraScanner();
                                        } else {
                                            setScannerActive(true);
                                        }
                                    }}
                                >
                                    {scannerActive ? (
                                        <>
                                            <CameraOff className="h-4 w-4" />
                                            Tắt Camera
                                        </>
                                    ) : (
                                        <>
                                            <Camera className="h-4 w-4" />
                                            Bật Camera
                                        </>
                                    )}
                                </Button>
                            </div>

                            {scannerActive && (
                                <div
                                    id="ecobite-qr-reader"
                                    className="mt-4 overflow-hidden rounded-xl border border-gray-200 bg-black/5"
                                />
                            )}

                            {cameraError && (
                                <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
                                    {cameraError}
                                </p>
                            )}
                        </Card>

                        {/* Manual Payload Paste Card */}
                        <Card className="p-5">
                            <form onSubmit={handleVerifySubmit} className="space-y-4">
                                <div>
                                    <label
                                        htmlFor="qr-token-input"
                                        className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold text-gray-800"
                                    >
                                        <QrCode className="h-4 w-4 text-emerald-600" />
                                        Hoặc dán chuỗi QR Payload để kiểm tra
                                    </label>
                                    <textarea
                                        id="qr-token-input"
                                        rows={3}
                                        value={qrToken}
                                        onChange={(e) => setQrToken(e.target.value)}
                                        placeholder="ecobite://pickup?order_id=...&nonce=...&sig=..."
                                        className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2.5 font-mono text-xs text-gray-900 placeholder:text-gray-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                                    />
                                </div>

                                <div className="flex flex-col gap-3">
                                    <span className="text-xs text-gray-500">
                                        Mẹo demo: Dán lại cùng 1 chuỗi QR sau khi xác thực thành công để kiểm chứng Anti-Replay.
                                    </span>
                                    <Button
                                        type="submit"
                                        isLoading={verifyMutation.isPending}
                                        className="w-full"
                                    >
                                        <ShieldCheck className="h-4 w-4" />
                                        Xác thực & Hoàn tất đơn
                                    </Button>
                                </div>
                            </form>
                        </Card>

                        {/* Verification Success Result */}
                        {verificationResult && (
                            <Card className="border-emerald-300 bg-emerald-50/70 p-5">
                                <div className="flex items-start gap-3">
                                    <CheckCircle2 className="mt-0.5 h-6 w-6 shrink-0 text-emerald-600" />
                                    <div className="flex-1 space-y-2">
                                        <div className="flex flex-wrap items-center gap-2">
                                            <h3 className="text-base font-bold text-emerald-900">
                                                Giao món thành công!
                                            </h3>
                                            <Badge variant="success">
                                                {verificationResult.status}
                                            </Badge>
                                        </div>
                                        <p className="text-xs text-emerald-800">
                                            {verificationResult.message}
                                        </p>

                                        <div className="mt-2 grid gap-2 rounded-xl border border-emerald-200 bg-white p-3 text-xs sm:grid-cols-3">
                                            <div>
                                                <p className="text-gray-500">Mã đơn</p>
                                                <p className="font-mono font-bold text-gray-900">
                                                    {verificationResult.order_code}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">Điểm Xanh</p>
                                                <p className="inline-flex items-center gap-1 font-bold text-emerald-700">
                                                    <Sparkles className="h-3.5 w-3.5" />+
                                                    {verificationResult.points_awarded}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">CO₂ cứu</p>
                                                <p className="inline-flex items-center gap-1 font-bold text-emerald-700">
                                                    <Leaf className="h-3.5 w-3.5" />
                                                    {Number(verificationResult.co2_saved_kg).toFixed(
                                                        2
                                                    )}{' '}
                                                    kg
                                                </p>
                                            </div>
                                        </div>

                                        {verificationResult.order && (
                                            <p className="text-xs text-emerald-700">
                                                Số lượng: {verificationResult.order.quantity} suất •
                                                Tổng tiền:{' '}
                                                {formatVND(verificationResult.order.total_amount)}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </Card>
                        )}

                        {/* Verification Error / Anti-Replay Block */}
                        {verificationError && (
                            <Card className="border-red-300 bg-red-50 p-5">
                                <div className="flex items-start gap-3">
                                    <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
                                    <div>
                                        <h3 className="text-sm font-bold text-red-900">
                                            Từ chối xác thực mã QR
                                        </h3>
                                        <p className="mt-1 text-xs text-red-700">
                                            {verificationError}
                                        </p>
                                    </div>
                                </div>
                            </Card>
                        )}
                    </div>

                    {/* Right Column: Store Orders Table */}
                    <div className="lg:col-span-7">
                        <Card className="p-5">
                            <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                <div className="flex items-center gap-2">
                                    <ClipboardList className="h-5 w-5 text-emerald-600" />
                                    <div>
                                        <h2 className="text-base font-bold text-gray-900">
                                            Danh sách đơn hàng của quán
                                        </h2>
                                        <p className="text-xs text-gray-500">
                                            Theo dõi đơn chờ giao và lịch sử giao món đã xác thực.
                                        </p>
                                    </div>
                                </div>
                                {myStore && (
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={() => void refetchOrders()}
                                    >
                                        <RefreshCw
                                            className={`h-4 w-4 ${ordersFetching ? 'animate-spin' : ''}`}
                                        />
                                        Làm mới
                                    </Button>
                                )}
                            </div>

                            {/* Status Filter Tabs */}
                            <div className="mb-4 flex flex-wrap gap-2">
                                {[
                                    {
                                        key: 'PENDING_PICKUP' as const,
                                        label: `Chờ giao (${pendingCount})`,
                                    },
                                    {
                                        key: 'COMPLETED' as const,
                                        label: `Đã hoàn thành (${completedCount})`,
                                    },
                                    {
                                        key: 'ALL' as const,
                                        label: `Tất cả (${storeOrders.length})`,
                                    },
                                ].map((tab) => (
                                    <button
                                        key={tab.key}
                                        type="button"
                                        onClick={() => setOrderTab(tab.key)}
                                        className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition-colors ${orderTab === tab.key
                                                ? 'bg-emerald-600 text-white'
                                                : 'border border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                                            }`}
                                    >
                                        {tab.label}
                                    </button>
                                ))}
                            </div>

                            {storeLoading || ordersLoading ? (
                                <div className="space-y-3">
                                    {[1, 2, 3].map((row) => (
                                        <div
                                            key={row}
                                            className="h-14 animate-pulse rounded-lg bg-gray-100"
                                        />
                                    ))}
                                </div>
                            ) : storeError ? (
                                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
                                    Không tìm thấy hồ sơ cửa hàng gắn với tài khoản hiện tại. Bạn vẫn
                                    có thể quét hoặc dán mã QR thủ công ở cột bên trái.
                                </div>
                            ) : ordersError ? (
                                <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-700">
                                    {extractApiErrorMessage(
                                        ordersError,
                                        'Không thể tải danh sách đơn hàng của cửa hàng.'
                                    )}
                                </div>
                            ) : filteredOrders.length === 0 ? (
                                <div className="rounded-xl border border-dashed border-gray-200 py-12 text-center">
                                    <ClipboardList className="mx-auto mb-2 h-8 w-8 text-gray-300" />
                                    <p className="text-sm font-semibold text-gray-700">
                                        Chưa có đơn hàng nào ở mục này
                                    </p>
                                    <p className="mt-1 text-xs text-gray-500">
                                        Các đơn mới đặt từ khách hàng sẽ xuất hiện tại đây.
                                    </p>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200 text-left text-xs">
                                        <thead>
                                            <tr className="bg-gray-50 text-[11px] font-semibold uppercase tracking-wide text-gray-500">
                                                <th className="px-3 py-2.5">Mã đơn & Món ăn</th>
                                                <th className="px-3 py-2.5">SL / Tổng tiền</th>
                                                <th className="px-3 py-2.5">Thanh toán</th>
                                                <th className="px-3 py-2.5">Trạng thái</th>
                                                <th className="px-3 py-2.5">Hạn lấy món</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100 bg-white">
                                            {filteredOrders.map((order) => {
                                                const statusBadge = getOrderStatusBadge(
                                                    order.status
                                                );
                                                return (
                                                    <tr
                                                        key={order.id}
                                                        className="hover:bg-gray-50/80"
                                                    >
                                                        <td className="px-3 py-3">
                                                            <p className="font-mono font-semibold text-gray-900">
                                                                {order.order_code}
                                                            </p>
                                                            <p className="mt-0.5 text-gray-600">
                                                                {order.dish_name ??
                                                                    'Suất ăn giải cứu'}
                                                            </p>
                                                        </td>
                                                        <td className="whitespace-nowrap px-3 py-3">
                                                            <p className="font-semibold text-emerald-700">
                                                                {formatVND(order.total_amount)}
                                                            </p>
                                                            <p className="text-gray-500">
                                                                {order.quantity} suất
                                                            </p>
                                                        </td>
                                                        <td className="whitespace-nowrap px-3 py-3">
                                                            <Badge
                                                                variant={getPaymentBadgeVariant(
                                                                    order.payment_status
                                                                )}
                                                            >
                                                                {order.payment_method} •{' '}
                                                                {order.payment_status}
                                                            </Badge>
                                                        </td>
                                                        <td className="whitespace-nowrap px-3 py-3">
                                                            <Badge variant={statusBadge.variant}>
                                                                {statusBadge.label}
                                                            </Badge>
                                                        </td>
                                                        <td className="whitespace-nowrap px-3 py-3 text-gray-500">
                                                            <span className="inline-flex items-center gap-1">
                                                                <Clock className="h-3.5 w-3.5 text-gray-400" />
                                                                {formatDateTime(
                                                                    order.pickup_deadline
                                                                )}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </Card>
                    </div>
                </div>

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