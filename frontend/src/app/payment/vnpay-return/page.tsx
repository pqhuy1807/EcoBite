'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
    AlertCircle,
    ArrowRight,
    CheckCircle2,
    Loader2,
    Receipt,
    ShieldCheck,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { extractApiErrorMessage } from '@/lib/api-client';
import { formatVND } from '@/lib/utils';
import { paymentService } from '@/services/payment.service';
import type { VNPayReturnResponse } from '@/types/api';

function VnpayReturnContent() {
    const searchParams = useSearchParams();
    const [loading, setLoading] = useState(true);
    const [result, setResult] = useState<VNPayReturnResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const responseCode = searchParams.get('vnp_ResponseCode');
    const rawAmount = searchParams.get('vnp_Amount');
    const bankCode = searchParams.get('vnp_BankCode');
    const orderInfo = searchParams.get('vnp_OrderInfo');
    const parsedAmount = rawAmount ? Number(rawAmount) / 100 : null;

    useEffect(() => {
        const queryParams: Record<string, string> = {};
        searchParams.forEach((value, key) => {
            queryParams[key] = value;
        });

        if (Object.keys(queryParams).length === 0) {
            setError('Không tìm thấy tham số giao dịch từ cổng thanh toán VNPay.');
            setLoading(false);
            return;
        }

        let cancelled = false;

        const verify = async () => {
            setLoading(true);
            setError(null);
            try {
                const res = await paymentService.verifyVnpayReturn(queryParams);
                if (!cancelled) {
                    setResult(res);
                }
            } catch (err: unknown) {
                if (!cancelled) {
                    setError(
                        extractApiErrorMessage(
                            err,
                            'Không thể xác thực chữ ký giao dịch VNPay. Vui lòng kiểm tra lại trong mục Đơn của tôi.'
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
    }, [searchParams]);

    const isPaymentSuccess = Boolean(
        result?.is_valid && (!responseCode || responseCode === '00')
    );

    return (
        <main className="mx-auto max-w-xl px-4 py-12 sm:px-6">
            <Card className="p-6 sm:p-8">
                {loading ? (
                    <div className="flex flex-col items-center py-8 text-center">
                        <Loader2 className="h-10 w-10 animate-spin text-emerald-600" />
                        <h1 className="mt-4 text-lg font-bold text-gray-900">
                            Đang xác thực giao dịch VNPay...
                        </h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Hệ thống đang kiểm tra chữ ký điện tử và cập nhật trạng thái đơn hàng.
                        </p>
                    </div>
                ) : error ? (
                    <div className="text-center">
                        <AlertCircle className="mx-auto h-12 w-12 text-red-500" />
                        <h1 className="mt-4 text-xl font-bold text-gray-900">
                            Xác thực thanh toán thất bại
                        </h1>
                        <p className="mt-2 text-sm text-red-700">{error}</p>
                        <div className="mt-6 flex flex-wrap justify-center gap-3">
                            <Link href="/orders">
                                <Button>Kiểm tra Đơn của tôi</Button>
                            </Link>
                            <Link href="/">
                                <Button variant="outline">Về Radar Quán</Button>
                            </Link>
                        </div>
                    </div>
                ) : (
                    <div>
                        <div className="text-center">
                            {isPaymentSuccess ? (
                                <CheckCircle2 className="mx-auto h-14 w-14 text-emerald-600" />
                            ) : (
                                <AlertCircle className="mx-auto h-14 w-14 text-red-500" />
                            )}

                            <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">
                                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                                {result?.is_valid
                                    ? 'Chữ ký VNPay hợp lệ'
                                    : 'Chữ ký không hợp lệ'}
                            </div>

                            <h1 className="mt-3 text-2xl font-bold text-gray-900">
                                {isPaymentSuccess
                                    ? 'Thanh toán thành công!'
                                    : 'Thanh toán chưa hoàn tất'}
                            </h1>

                            <p className="mt-1.5 text-sm text-gray-600">
                                {result?.message}
                            </p>
                        </div>

                        <div className="mt-6 space-y-2.5 rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm">
                            <div className="flex items-center gap-2 font-semibold text-gray-800">
                                <Receipt className="h-4 w-4 text-emerald-600" />
                                Chi tiết giao dịch
                            </div>

                            {result?.txn_ref && (
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-gray-500">Mã tham chiếu (TxnRef)</span>
                                    <span className="font-mono font-semibold text-gray-900">
                                        {result.txn_ref}
                                    </span>
                                </div>
                            )}

                            {parsedAmount !== null && !Number.isNaN(parsedAmount) && (
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-gray-500">Số tiền</span>
                                    <span className="font-bold text-emerald-700">
                                        {formatVND(parsedAmount)}
                                    </span>
                                </div>
                            )}

                            {bankCode && (
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-gray-500">Ngân hàng</span>
                                    <span className="font-medium text-gray-900">{bankCode}</span>
                                </div>
                            )}

                            {responseCode && (
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-gray-500">Mã phản hồi VNPay</span>
                                    <span className="font-mono text-gray-900">{responseCode}</span>
                                </div>
                            )}

                            {orderInfo && (
                                <div className="flex items-start justify-between gap-4">
                                    <span className="shrink-0 text-gray-500">Nội dung</span>
                                    <span className="text-right text-gray-800">{orderInfo}</span>
                                </div>
                            )}
                        </div>

                        <div className="mt-6 flex flex-wrap justify-center gap-3">
                            <Link href="/orders">
                                <Button>
                                    Xem đơn hàng & Mã QR
                                    <ArrowRight className="h-4 w-4" />
                                </Button>
                            </Link>
                            <Link href="/">
                                <Button variant="outline">Tiếp tục giải cứu món</Button>
                            </Link>
                        </div>
                    </div>
                )}
            </Card>
        </main>
    );
}

export default function VnpayReturnPage() {
    return (
        <Suspense
            fallback={
                <main className="mx-auto max-w-xl px-4 py-12 text-center text-sm text-gray-500">
                    Đang tải kết quả giao dịch...
                </main>
            }
        >
            <VnpayReturnContent />
        </Suspense>
    );
}