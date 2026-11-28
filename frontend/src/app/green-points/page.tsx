'use client';

import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    Award,
    Check,
    Clock,
    Copy,
    Gift,
    History,
    Leaf,
    RefreshCw,
    Sparkles,
    Ticket,
    Utensils,
} from 'lucide-react';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Toast } from '@/components/ui/Toast';
import { extractApiErrorMessage } from '@/lib/api-client';
import { formatDateTime, formatVND } from '@/lib/utils';
import { gamificationService } from '@/services/gamification.service';
import type { VoucherResponse } from '@/types/api';

const CONSUMER_ONLY_ROLES = ['CONSUMER'];

type ActiveTab = 'catalog' | 'my-vouchers' | 'ledger';

function formatActionLabel(actionType: string): string {
    switch (actionType) {
        case 'ORDER_COMPLETED':
        case 'RESCUE_ORDER':
            return 'Giải cứu đơn hàng';
        case 'VOUCHER_REDEEM':
        case 'REDEEM_VOUCHER':
            return 'Đổi Voucher ưu đãi';
        case 'BONUS':
            return 'Điểm thưởng';
        default:
            return actionType;
    }
}

export default function GreenPointsPage() {
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState<ActiveTab>('catalog');
    const [copiedCode, setCopiedCode] = useState<string | null>(null);
    const [toast, setToast] = useState<{
        message: string;
        type: 'success' | 'error' | 'info';
    } | null>(null);

    const summaryQuery = useQuery({
        queryKey: ['green-points-summary'],
        queryFn: () => gamificationService.getMyGreenPoints(30),
    });

    const catalogQuery = useQuery({
        queryKey: ['vouchers-catalog'],
        queryFn: () => gamificationService.listAvailableVouchers(),
    });

    const myVouchersQuery = useQuery({
        queryKey: ['my-vouchers'],
        queryFn: () => gamificationService.listMyVouchers(0, 50),
    });

    const redeemMutation = useMutation({
        mutationFn: (voucherId: string) => gamificationService.redeemVoucher(voucherId),
        onSuccess: (res) => {
            setToast({
                message: `Đổi thành công voucher ${res.voucher_code} (-${res.points_deducted} điểm). Số dư còn ${res.remaining_balance} điểm.`,
                type: 'success',
            });
            void queryClient.invalidateQueries({ queryKey: ['green-points-summary'] });
            void queryClient.invalidateQueries({ queryKey: ['my-vouchers'] });
            void queryClient.invalidateQueries({ queryKey: ['vouchers-catalog'] });
            setActiveTab('my-vouchers');
        },
        onError: (err) => {
            setToast({
                message: extractApiErrorMessage(err, 'Không thể đổi voucher này. Vui lòng thử lại.'),
                type: 'error',
            });
        },
    });

    const handleRedeem = (voucher: VoucherResponse) => {
        if (!window.confirm(`Dùng ${voucher.points_required} Điểm Xanh để đổi voucher "${voucher.title}"?`)) {
            return;
        }
        redeemMutation.mutate(voucher.id);
    };

    const handleCopyCode = async (code: string) => {
        try {
            await navigator.clipboard.writeText(code);
            setCopiedCode(code);
            setToast({ message: `Đã sao chép mã voucher ${code}.`, type: 'success' });
            setTimeout(() => setCopiedCode(null), 2000);
        } catch {
            setToast({ message: 'Không thể sao chép tự động.', type: 'error' });
        }
    };

    const handleRefreshAll = () => {
        void summaryQuery.refetch();
        void catalogQuery.refetch();
        void myVouchersQuery.refetch();
    };

    const summary = summaryQuery.data;
    const balancePoints = summary?.balance_points ?? 0;
    const isRefreshing =
        summaryQuery.isFetching || catalogQuery.isFetching || myVouchersQuery.isFetching;

    return (
        <AuthGuard allowedRoles={CONSUMER_ONLY_ROLES}>
            <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                            <Sparkles className="h-3.5 w-3.5" />
                            Hành trình Sống Xanh • Đổi thưởng ưu đãi
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            Điểm Xanh &amp; Kho Voucher
                        </h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Theo dõi lượng CO₂ bạn đã giảm phát thải và đổi Điểm Xanh lấy mã giảm giá.
                        </p>
                    </div>

                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleRefreshAll}
                    >
                        <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                        Làm mới
                    </Button>
                </div>

                {summaryQuery.error && (
                    <Card className="mb-6 border-red-200 bg-red-50 p-4 text-sm text-red-700">
                        {extractApiErrorMessage(
                            summaryQuery.error,
                            'Không thể tải dữ liệu Điểm Xanh của bạn.'
                        )}
                    </Card>
                )}

                <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <Card className="border-emerald-200 bg-emerald-50/70 p-5">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-emerald-800">
                                Số dư Điểm Xanh
                            </span>
                            <Sparkles className="h-5 w-5 text-emerald-600" />
                        </div>
                        <p className="mt-2 text-3xl font-extrabold text-emerald-900">
                            {summaryQuery.isLoading ? '...' : balancePoints.toLocaleString('vi-VN')}
                        </p>
                        <p className="mt-1 text-xs text-emerald-700">điểm khả dụng</p>
                    </Card>

                    <Card className="p-5">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-gray-500">
                                Danh hiệu hiện tại
                            </span>
                            <Award className="h-5 w-5 text-amber-500" />
                        </div>
                        <p className="mt-2 text-lg font-bold text-gray-900">
                            {summaryQuery.isLoading ? '...' : summary?.rank_title ?? 'Tân binh Xanh'}
                        </p>
                        <p className="mt-1 text-xs text-gray-500">Xếp hạng đóng góp môi trường</p>
                    </Card>

                    <Card className="p-5">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-gray-500">
                                CO₂ đã cắt giảm
                            </span>
                            <Leaf className="h-5 w-5 text-emerald-600" />
                        </div>
                        <p className="mt-2 text-3xl font-extrabold text-gray-900">
                            {summaryQuery.isLoading
                                ? '...'
                                : Number(summary?.total_co2_saved_kg ?? 0).toFixed(2)}
                        </p>
                        <p className="mt-1 text-xs text-gray-500">kg CO₂e tiết kiệm được</p>
                    </Card>

                    <Card className="p-5">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-gray-500">
                                Suất ăn đã giải cứu
                            </span>
                            <Utensils className="h-5 w-5 text-orange-500" />
                        </div>
                        <p className="mt-2 text-3xl font-extrabold text-gray-900">
                            {summaryQuery.isLoading ? '...' : summary?.total_meals_saved ?? 0}
                        </p>
                        <p className="mt-1 text-xs text-gray-500">suất ăn hoàn tất nhận món</p>
                    </Card>
                </div>

                <div className="mb-6 flex flex-wrap gap-2 border-b border-gray-200 pb-3">
                    <button
                        type="button"
                        onClick={() => setActiveTab('catalog')}
                        className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition-colors ${activeTab === 'catalog'
                                ? 'bg-emerald-600 text-white'
                                : 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                            }`}
                    >
                        <Gift className="h-4 w-4" />
                        Đổi Voucher ({catalogQuery.data?.length ?? 0})
                    </button>

                    <button
                        type="button"
                        onClick={() => setActiveTab('my-vouchers')}
                        className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition-colors ${activeTab === 'my-vouchers'
                                ? 'bg-emerald-600 text-white'
                                : 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                            }`}
                    >
                        <Ticket className="h-4 w-4" />
                        Voucher của tôi ({myVouchersQuery.data?.length ?? 0})
                    </button>

                    <button
                        type="button"
                        onClick={() => setActiveTab('ledger')}
                        className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition-colors ${activeTab === 'ledger'
                                ? 'bg-emerald-600 text-white'
                                : 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                            }`}
                    >
                        <History className="h-4 w-4" />
                        Lịch sử điểm ({summary?.recent_ledger.length ?? 0})
                    </button>
                </div>

                {activeTab === 'catalog' && (
                    <div>
                        {catalogQuery.isLoading ? (
                            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                {[1, 2, 3].map((i) => (
                                    <Card key={i} className="h-44 animate-pulse bg-gray-100" />
                                ))}
                            </div>
                        ) : (catalogQuery.data?.length ?? 0) === 0 ? (
                            <Card className="border-dashed p-10 text-center">
                                <Gift className="mx-auto h-10 w-10 text-gray-300" />
                                <p className="mt-3 text-sm font-semibold text-gray-800">
                                    Hiện chưa có voucher nào đang mở đổi
                                </p>
                                <p className="mt-1 text-xs text-gray-500">
                                    Hãy tiếp tục tích lũy Điểm Xanh từ các đơn giải cứu món ăn nhé.
                                </p>
                            </Card>
                        ) : (
                            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                {catalogQuery.data?.map((voucher) => {
                                    const canAfford = balancePoints >= voucher.points_required;
                                    const isRedeeming =
                                        redeemMutation.isPending &&
                                        redeemMutation.variables === voucher.id;

                                    return (
                                        <Card
                                            key={voucher.id}
                                            className="flex flex-col justify-between p-5"
                                        >
                                            <div className="space-y-2">
                                                <div className="flex items-start justify-between gap-2">
                                                    <Badge variant="success">
                                                        Giảm {formatVND(voucher.discount_amount)}
                                                    </Badge>
                                                    <span className="font-mono text-xs font-semibold text-gray-500">
                                                        {voucher.code}
                                                    </span>
                                                </div>

                                                <h3 className="text-base font-bold text-gray-900">
                                                    {voucher.title}
                                                </h3>

                                                {voucher.description && (
                                                    <p className="text-xs text-gray-600">
                                                        {voucher.description}
                                                    </p>
                                                )}

                                                <div className="space-y-1 pt-1 text-xs text-gray-500">
                                                    {Number(voucher.min_order_amount) > 0 && (
                                                        <p>
                                                            Đơn tối thiểu:{' '}
                                                            <span className="font-semibold text-gray-700">
                                                                {formatVND(voucher.min_order_amount)}
                                                            </span>
                                                        </p>
                                                    )}
                                                    <p className="inline-flex items-center gap-1">
                                                        <Clock className="h-3.5 w-3.5" />
                                                        HSD: {formatDateTime(voucher.expires_at)}
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="mt-5 flex items-center justify-between border-t border-gray-100 pt-4">
                                                <span className="inline-flex items-center gap-1 text-sm font-bold text-emerald-700">
                                                    <Sparkles className="h-4 w-4" />
                                                    {voucher.points_required} điểm
                                                </span>

                                                <Button
                                                    type="button"
                                                    size="sm"
                                                    disabled={!canAfford || isRedeeming}
                                                    isLoading={isRedeeming}
                                                    onClick={() => handleRedeem(voucher)}
                                                >
                                                    {canAfford ? 'Đổi ngay' : 'Chưa đủ điểm'}
                                                </Button>
                                            </div>
                                        </Card>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'my-vouchers' && (
                    <div>
                        {myVouchersQuery.isLoading ? (
                            <div className="space-y-3">
                                {[1, 2].map((i) => (
                                    <Card key={i} className="h-24 animate-pulse bg-gray-100" />
                                ))}
                            </div>
                        ) : (myVouchersQuery.data?.length ?? 0) === 0 ? (
                            <Card className="border-dashed p-10 text-center">
                                <Ticket className="mx-auto h-10 w-10 text-gray-300" />
                                <p className="mt-3 text-sm font-semibold text-gray-800">
                                    Bạn chưa đổi voucher nào
                                </p>
                                <p className="mt-1 text-xs text-gray-500">
                                    Chuyển sang mục Đổi Voucher để dùng Điểm Xanh nhận ưu đãi.
                                </p>
                            </Card>
                        ) : (
                            <div className="space-y-3">
                                {myVouchersQuery.data?.map((uv) => {
                                    const code = uv.voucher?.code ?? uv.voucher_id.slice(0, 8);
                                    const isCopied = copiedCode === code;

                                    return (
                                        <Card key={uv.id} className="p-4">
                                            <div className="flex flex-wrap items-center justify-between gap-4">
                                                <div className="space-y-1">
                                                    <div className="flex flex-wrap items-center gap-2">
                                                        <h3 className="font-bold text-gray-900">
                                                            {uv.voucher?.title ?? 'Voucher ưu đãi EcoBite'}
                                                        </h3>
                                                        <Badge variant={uv.is_used ? 'neutral' : 'success'}>
                                                            {uv.is_used ? 'Đã sử dụng' : 'Sẵn sàng dùng'}
                                                        </Badge>
                                                    </div>

                                                    {uv.voucher && (
                                                        <p className="text-xs font-semibold text-emerald-700">
                                                            Giảm {formatVND(uv.voucher.discount_amount)}
                                                            {Number(uv.voucher.min_order_amount) > 0
                                                                ? ` • Đơn từ ${formatVND(uv.voucher.min_order_amount)}`
                                                                : ''}
                                                        </p>
                                                    )}

                                                    <p className="text-xs text-gray-500">
                                                        Đổi lúc: {formatDateTime(uv.claimed_at)}
                                                        {uv.voucher?.expires_at
                                                            ? ` • HSD: ${formatDateTime(uv.voucher.expires_at)}`
                                                            : ''}
                                                    </p>
                                                </div>

                                                <div className="flex items-center gap-2">
                                                    <span className="rounded-lg border border-dashed border-emerald-300 bg-emerald-50 px-3 py-1.5 font-mono text-xs font-bold text-emerald-800">
                                                        {code}
                                                    </span>
                                                    <Button
                                                        type="button"
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => void handleCopyCode(code)}
                                                    >
                                                        {isCopied ? (
                                                            <>
                                                                <Check className="h-3.5 w-3.5" />
                                                                Đã chép
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Copy className="h-3.5 w-3.5" />
                                                                Sao chép
                                                            </>
                                                        )}
                                                    </Button>
                                                </div>
                                            </div>
                                        </Card>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'ledger' && (
                    <div>
                        {(summary?.recent_ledger.length ?? 0) === 0 ? (
                            <Card className="border-dashed p-10 text-center">
                                <History className="mx-auto h-10 w-10 text-gray-300" />
                                <p className="mt-3 text-sm font-semibold text-gray-800">
                                    Chưa có lịch sử giao dịch Điểm Xanh
                                </p>
                                <p className="mt-1 text-xs text-gray-500">
                                    Điểm Xanh sẽ được cộng tự động sau khi quán quét mã QR giao món thành công.
                                </p>
                            </Card>
                        ) : (
                            <Card className="divide-y divide-gray-100 overflow-hidden">
                                {summary?.recent_ledger.map((entry) => {
                                    const isPositive = entry.points_change >= 0;

                                    return (
                                        <div
                                            key={entry.id}
                                            className="flex flex-wrap items-center justify-between gap-3 p-4"
                                        >
                                            <div className="space-y-0.5">
                                                <p className="text-sm font-semibold text-gray-900">
                                                    {formatActionLabel(entry.action_type)}
                                                </p>
                                                {entry.note && (
                                                    <p className="text-xs text-gray-600">{entry.note}</p>
                                                )}
                                                <p className="text-xs text-gray-400">
                                                    {formatDateTime(entry.created_at)}
                                                    {Number(entry.co2_saved_kg) > 0
                                                        ? ` • Tiết kiệm ${Number(entry.co2_saved_kg).toFixed(2)} kg CO₂`
                                                        : ''}
                                                </p>
                                            </div>

                                            <div className="text-right">
                                                <p
                                                    className={`text-sm font-bold ${isPositive ? 'text-emerald-700' : 'text-red-600'
                                                        }`}
                                                >
                                                    {isPositive ? '+' : ''}
                                                    {entry.points_change} điểm
                                                </p>
                                                <p className="text-xs text-gray-500">
                                                    Số dư: {entry.balance_after}
                                                </p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </Card>
                        )}
                    </div>
                )}

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