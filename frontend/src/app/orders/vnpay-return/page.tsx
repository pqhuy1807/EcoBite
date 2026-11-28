'use client';

import React, { Suspense, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
    AlertCircle,
    ArrowLeft,
    CheckCircle2,
    Loader2,
    Receipt,
    ShoppingBag,
    XCircle,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { extractApiErrorMessage } from '@/lib/api-client';
import { formatVND } from '@/lib/utils';
import { paymentService, type VNPayReturnResponse } from '@/services/payment.service';

function VnpayReturnContent() {
    const searchParams = useSearchParams();
    const queryString = searchParams.toString();

    const queryRecord = useMemo(() => {
        const params: Record<string, string> = {};
        const parsed = new URLSearchParams(queryString);
        parsed.forEach((value, key) => {
            params[key] = value;
        });
        return params;
    }, [queryString]);

    const [loading, setLoading] = useState(true);
    const [result, setResult] = useState<VNPayReturnResponse | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const responseCode = queryRecord.vnp_ResponseCode ?? '';
    const bankCode = queryRecord.vnp_BankCode ?? '';
    const rawAmount = Number(queryRecord.vnp_Amount ?? '0');
    const amountVnd = Number.isFinite(rawAmount) && rawAmount > 0 ? rawAmount / 100 : null;
    const txnRefFromQuery = queryRecord.vnp_TxnRef ?? null;

    useEffect(() => {
        if (Object.keys(queryRecord).length === 0) {
            setLoading(false);
            setErrorMessage('Thiếu tham số phản hồi từ cổng thanh toán VNPay.');
            return;
        }

        let cancelled = false;
        const verify = async () => {
            setLoading(true);
            setErrorMessage(null);
            try {
                const data = await paymentService.verifyVnpayReturn(queryRecord);
                if (!cancelled) {
                    setResult(data);
                }
            } catch (err) {
                if (!cancelled) {
                    setErrorMessage(
                        extractApiErrorMessage(
                            err,
                            'Không thể xác thực chữ ký giao dịch VNPay từ máy chủ.'
                        )
                    );
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        };

        void verify();
        return () => {
            cancelled = true;
        };
    }, [queryRecord]);

    const isSuccess = Boolean(result?.is_valid && responseCode === '00');
    const displayTxnRef = result?.txn_ref ?? txnRefFromQuery;

    return (
        <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
            <Card className="p-6 sm:p-8">
                {loading ? (
                    <div className="flex flex-col items-center py-10 text-center">
                        <Loader2 className="mb-3 h-10 w-10 animate-spin text-emerald-600" />
                        <h1 className="text-lg font-bold text-gray-900">
                            Đang xác thực kết quả thanh toán VNPay...
                        </h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Hệ thống đang đối chiếu chữ ký bảo mật HMAC-SHA512 với máy chủ.
                        </p>
                    </div>
                ) : errorMessage ? (
                    <div className="space-y-5 text-center">
                        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600">
                            <AlertCircle className="h-8 w-8" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">
                                Không thể xác thực giao dịch
                            </h1>
                            <p className="mt-2 text-sm text-red-600">{errorMessage}</p>
                        </div>
                        <div className="flex flex-wrap justify-center gap-3 pt-2">
                            <Link
                                href="/orders"
                                className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
                            >
                                <ShoppingBag className="h-4 w-4" />
                                Kiểm tra đơn của tôi
                            </Link>
                            <Link
                                href="/"
                                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                            >
                                <ArrowLeft className="h-4 w-4" />
                                Quay lại Radar
                            </Link>
                        </div>
                    </div>
                ) : isSuccess ? (
                    <div className="space-y-6">
                        <div className="text-center">
                            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                                <CheckCircle2 className="h-8 w-8" />
                            </div>
                            <Badge variant="success">Chữ ký HMAC-SHA512 hợp lệ</Badge>
                            <h1 className="mt-2 text-2xl font-bold text-gray-900">
                                Thanh toán VNPay thành công!
                            </h1>
                            <p className="mt-1 text-sm text-gray-600">
                                {result?.message ||
                                    'Giao dịch đã được xác nhận. Bạn có thể mở mã QR để nhận món tại quán.'}
                            </p>
                        </div>

                        <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4">
                            <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-emerald-800">
                                <Receipt className="h-4 w-4" />
                                Thông tin giao dịch
                            </div>
                            <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                                <div>
                                    <dt className="text-xs text-gray-500">Mã tham chiếu (TxnRef)</dt>
                                    <dd className="font-mono font-semibold text-gray-900">
                                        {displayTxnRef ?? '—'}
                                    </dd>
                                </div>
                                {amountVnd !== null && (
                                    <div>
                                        <dt className="text-xs text-gray-500">Số tiền thanh toán</dt>
                                        <dd className="font-bold text-emerald-700">
                                            {formatVND(amountVnd)}
                                        </dd>
                                    </div>
                                )}
                                {bankCode && (
                                    <div>
                                        <dt className="text-xs text-gray-500">Ngân hàng</dt>
                                        <dd className="font-medium text-gray-900">{bankCode}</dd>
                                    </div>
                                )}
                                <div>
                                    <dt className="text-xs text-gray-500">Mã phản hồi VNPay</dt>
                                    <dd className="font-mono font-medium text-emerald-700">
                                        {responseCode} (Thành công)
                                    </dd>
                                </div>
                            </dl>
                        </div>

                        <div className="flex flex-wrap justify-center gap-3">
                            <Link
                                href="/orders"
                                className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700"
                            >
                                <ShoppingBag className="h-4 w-4" />
                                Đi tới Đơn của tôi để lấy mã QR
                            </Link>
                            <Link
                                href="/"
                                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                            >
                                <ArrowLeft className="h-4 w-4" />
                                Về Radar
                            </Link>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6">
                        <div className="text-center">
                            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600">
                                <XCircle className="h-8 w-8" />
                            </div>
                            <Badge variant="danger">
                                {result?.is_valid
                                    ? `Thanh toán chưa thành công (Mã ${responseCode || 'N/A'})`
                                    : 'Chữ ký không hợp lệ'}
                            </Badge>
                            <h1 className="mt-2 text-2xl font-bold text-gray-900">
                                Giao dịch VNPay thất bại hoặc đã bị hủy
                            </h1>
                            <p className="mt-1 text-sm text-gray-600">
                                {result?.message ||
                                    'Thanh toán không hoàn tất. Nếu đơn bị hủy, tồn kho suất ăn đã được hệ thống hoàn lại cho cửa hàng.'}
                            </p>
                        </div>

                        {displayTxnRef && (
                            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-center text-sm">
                                <p className="text-xs text-gray-500">Mã tham chiếu (TxnRef)</p>
                                <p className="mt-0.5 font-mono font-semibold text-gray-900">
                                    {displayTxnRef}
                                </p>
                            </div>
                        )}

                        <div className="flex flex-wrap justify-center gap-3">
                            <Link
                                href="/orders"
                                className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
                            >
                                <ShoppingBag className="h-4 w-4" />
                                Xem đơn & Thanh toán lại
                            </Link>
                            <Link
                                href="/"
                                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                            >
                                <ArrowLeft className="h-4 w-4" />
                                Quay lại Radar
                            </Link>
                        </div>
                    </div>
                )}
            </Card>
        </div>
    );
}

export default function OrdersVnpayReturnPage() {
    return (
        <Suspense
            fallback={
                <div className="mx-auto flex max-w-2xl flex-col items-center px-4 py-16 text-center">
                    <Loader2 className="mb-3 h-8 w-8 animate-spin text-emerald-600" />
                    <p className="text-sm text-gray-500">Đang tải thông tin thanh toán...</p>
                </div>
            }
        >
            <VnpayReturnContent />
        </Suspense>
    );
}