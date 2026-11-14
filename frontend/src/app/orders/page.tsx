'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    Check,
    Clock,
    Copy,
    Leaf,
    QrCode,
    RefreshCw,
    ShoppingBag,
    XCircle,
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Toast } from '@/components/ui/Toast';
import { extractApiErrorMessage } from '@/lib/api-client';
import { formatDateTime, formatVND } from '@/lib/utils';
import { orderService } from '@/services/order.service';
import type { OrderResponse, OrderStatus, QRPayloadResponse } from '@/types/api';

const CONSUMER_ROLES = ['CONSUMER', 'ADMIN'];

const STATUS_TABS: Array<{ key: 'ALL' | OrderStatus; label: string }> = [
    { key: 'ALL', label: 'Tất cả' },
    { key: 'CONFIRMED', label: 'Đã xác nhận' },
    { key: 'READY_FOR_PICKUP', label: 'Chờ lấy món' },
    { key: 'COMPLETED', label: 'Hoàn thành' },
    { key: 'CANCELLED', label: 'Đã hủy' },
];

function getStatusBadge(status: OrderStatus): {
    label: string;
    variant: 'success' | 'warning' | 'danger' | 'info' | 'neutral';
} {
    switch (status) {
        case 'CONFIRMED':
            return { label: 'Đã xác nhận', variant: 'info' };
        case 'READY_FOR_PICKUP':
            return { label: 'Sẵn sàng lấy món', variant: 'warning' };
        case 'COMPLETED':
            return { label: 'Đã hoàn thành', variant: 'success' };
        case 'CANCELLED':
            return { label: 'Đã hủy', variant: 'danger' };
        case 'EXPIRED':
            return { label: 'Hết hạn', variant: 'neutral' };
        default:
            return { label: status, variant: 'neutral' };
    }
}

export default function MyOrdersPage() {
    const queryClient = useQueryClient();
    const [statusFilter, setStatusFilter] = useState<'ALL' | OrderStatus>('ALL');
    const [qrData, setQrData] = useState<QRPayloadResponse | null>(null);
    const [qrOrder, setQrOrder] = useState<OrderResponse | null>(null);
    const [copied, setCopied] = useState(false);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(
        null
    );

    const {
        data: orders = [],
        isLoading,
        isFetching,
        error,
        refetch,
    } = useQuery({
        queryKey: ['my-orders', statusFilter],
        queryFn: () =>
            orderService.getMyOrders(statusFilter === 'ALL' ? undefined : statusFilter),
    });

    const issueQrMutation = useMutation({
        mutationFn: (order: OrderResponse) => orderService.issueOrderQr(order.id),
        onSuccess: (data, order) => {
            setQrOrder(order);
            setQrData(data);
            setCopied(false);
        },
        onError: (err) => {
            setToast({
                message: extractApiErrorMessage(err, 'Không thể cấp mã QR cho đơn hàng này.'),
                type: 'error',
            });
        },
    });

    const cancelMutation = useMutation({
        mutationFn: (orderId: string) => orderService.cancelOrder(orderId),
        onSuccess: (updated) => {
            setToast({
                message: `Đã hủy đơn ${updated.order_code} và hoàn lại tồn kho cho quán.`,
                type: 'info',
            });
            queryClient.invalidateQueries({ queryKey: ['my-orders'] });
            queryClient.invalidateQueries({ queryKey: ['nearby-stores'] });
        },
        onError: (err) => {
            setToast({
                message: extractApiErrorMessage(err, 'Không thể hủy đơn hàng.'),
                type: 'error',
            });
        },
    });

    // If navigated with ?highlight=<orderId>, auto-open QR once orders load
    useEffect(() => {
        if (typeof window === 'undefined' || orders.length === 0) return;
        const params = new URLSearchParams(window.location.search);
        const highlightId = params.get('highlight');
        if (!highlightId) return;
        const matched = orders.find((o) => o.id === highlightId);
        if (matched && (matched.status === 'CONFIRMED' || matched.status === 'READY_FOR_PICKUP')) {
            issueQrMutation.mutate(matched);
            window.history.replaceState({}, '', '/orders');
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [orders]);

    const handleCopyPayload = async () => {
        if (!qrData?.qr_payload) return;
        try {
            await navigator.clipboard.writeText(qrData.qr_payload);
            setCopied(true);
            setToast({
                message: 'Đã sao chép chuỗi mã QR HMAC-SHA256.',
                type: 'success',
            });
            setTimeout(() => setCopied(false), 2000);
        } catch {
            setToast({
                message: 'Không thể tự động sao chép, vui lòng copy thủ công từ ô bên dưới.',
                type: 'error',
            });
        }
    };

    return (
        <AuthGuard allowedRoles={CONSUMER_ROLES}>
            <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Đơn giải cứu của tôi</h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Xuất trình mã QR động HMAC-SHA256 tại quầy cửa hàng để hoàn tất nhận món.
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => refetch()}
                        >
                            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
                            Làm mới
                        </Button>
                        <Link
                            href="/"
                            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                        >
                            <ShoppingBag className="h-4 w-4" />
                            Tìm thêm món
                        </Link>
                    </div>
                </div>

                {/* Status Filter Tabs */}
                <div className="mb-6 flex flex-wrap gap-2">
                    {STATUS_TABS.map((tab) => (
                        <button
                            key={tab.key}
                            type="button"
                            onClick={() => setStatusFilter(tab.key)}
                            className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${
                                statusFilter === tab.key
                                    ? 'bg-emerald-600 text-white'
                                    : 'border border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {isLoading && (
                    <div className="space-y-4">
                        {[1, 2].map((i) => (
                            <Card key={i} className="h-36 animate-pulse bg-gray-100 p-5" />
                        ))}
                    </div>
                )}

                {error && (
                    <Card className="border-red-200 bg-red-50 p-5 text-sm text-red-700">
                        {extractApiErrorMessage(error, 'Không thể tải danh sách đơn hàng.')}
                    </Card>
                )}

                {!isLoading && !error && orders.length === 0 && (
                    <Card className="p-10 text-center">
                        <ShoppingBag className="mx-auto mb-3 h-10 w-10 text-gray-300" />
                        <h2 className="text-base font-semibold text-gray-900">
                            Chưa có đơn hàng nào ở trạng thái này
                        </h2>
                        <p className="mt-1 text-sm text-gray-500">
                            Quay lại Radar để giải cứu những suất ăn giờ chót gần bạn.
                        </p>
                    </Card>
                )}

                <div className="space-y-4">
                    {orders.map((order) => {
                        const badge = getStatusBadge(order.status);
                        const canAct =
                            order.status === 'CONFIRMED' || order.status === 'READY_FOR_PICKUP';

                        return (
                            <Card key={order.id} className="p-5">
                                <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                                    <div className="space-y-2">
                                        <div className="flex flex-wrap items-center gap-2.5">
                                            <span className="font-mono text-base font-bold text-gray-900">
                                                {order.order_code}
                                            </span>
                                            <Badge variant={badge.variant}>{badge.label}</Badge>
                                            <Badge variant="neutral">
                                                {order.payment_method} • {order.payment_status}
                                            </Badge>
                                        </div>

                                        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600">
                                            <span>Số lượng: {order.quantity} suất</span>
                                            <span className="font-semibold text-emerald-700">
                                                Tổng tiền: {formatVND(order.total_amount)}
                                            </span>
                                            <span className="inline-flex items-center gap-1 text-emerald-700">
                                                <Leaf className="h-3.5 w-3.5" />
                                                {Number(order.co2_saved_kg).toFixed(2)} kg CO₂ (+
                                                {order.green_points_earned} điểm)
                                            </span>
                                        </div>

                                        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
                                            <span className="inline-flex items-center gap-1">
                                                <Clock className="h-3.5 w-3.5" />
                                                Hạn lấy món: {formatDateTime(order.pickup_deadline)}
                                            </span>
                                            <span>Tạo lúc: {formatDateTime(order.created_at)}</span>
                                        </div>
                                    </div>

                                    {canAct && (
                                        <div className="flex flex-wrap items-center gap-2">
                                            <Button
                                                type="button"
                                                size="sm"
                                                onClick={() => issueQrMutation.mutate(order)}
                                                isLoading={
                                                    issueQrMutation.isPending &&
                                                    issueQrMutation.variables?.id === order.id
                                                }
                                            >
                                                <QrCode className="h-4 w-4" />
                                                Xem mã QR
                                            </Button>
                                            <Button
                                                type="button"
                                                variant="outline"
                                                size="sm"
                                                className="border-red-200 text-red-600 hover:bg-red-50"
                                                onClick={() => cancelMutation.mutate(order.id)}
                                                isLoading={
                                                    cancelMutation.isPending &&
                                                    cancelMutation.variables === order.id
                                                }
                                            >
                                                <XCircle className="h-4 w-4" />
                                                Hủy đơn
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            </Card>
                        );
                    })}
                </div>

                {/* Dynamic QR Modal */}
                <Modal
                    isOpen={Boolean(qrData)}
                    onClose={() => {
                        setQrData(null);
                        setQrOrder(null);
                    }}
                    title={`Mã QR nhận món • ${qrData?.order_code ?? ''}`}
                >
                    {qrData && (
                        <div className="space-y-4 text-center">
                            <div className="mx-auto inline-flex rounded-2xl border border-emerald-100 bg-white p-4 shadow-sm">
                                <QRCodeSVG value={qrData.qr_payload} size={220} level="M" />
                            </div>

                            <div className="space-y-1 text-xs text-gray-600">
                                <p>
                                    Hiệu lực đến:{' '}
                                    <span className="font-semibold text-gray-900">
                                        {formatDateTime(qrData.expires_at)}
                                    </span>
                                </p>
                                {qrOrder && (
                                    <p>
                                        Giá trị đơn: {formatVND(qrOrder.total_amount)} •{' '}
                                        {qrOrder.quantity} suất
                                    </p>
                                )}
                                <p className="text-emerald-700">
                                    Mã dùng 1 lần (HMAC-SHA256 chống quét lại).
                                </p>
                            </div>

                            <div className="rounded-lg border border-gray-200 bg-gray-50 p-2.5 text-left">
                                <div className="mb-1 flex items-center justify-between">
                                    <span className="text-[11px] font-medium text-gray-500">
                                        Chuỗi QR Payload (dùng cho demo/máy quét thủ công)
                                    </span>
                                    <button
                                        type="button"
                                        onClick={handleCopyPayload}
                                        className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-100"
                                    >
                                        {copied ? (
                                            <>
                                                <Check className="h-3.5 w-3.5" />
                                                Đã copy
                                            </>
                                        ) : (
                                            <>
                                                <Copy className="h-3.5 w-3.5" />
                                                Sao chép
                                            </>
                                        )}
                                    </button>
                                </div>
                                <p className="break-all font-mono text-[11px] text-gray-700">
                                    {qrData.qr_payload}
                                </p>
                            </div>

                            <Button
                                type="button"
                                variant="outline"
                                className="w-full"
                                onClick={() => {
                                    setQrData(null);
                                    setQrOrder(null);
                                }}
                            >
                                Đóng
                            </Button>
                        </div>
                    )}
                </Modal>

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
