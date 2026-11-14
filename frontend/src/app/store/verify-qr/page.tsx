'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
    AlertCircle,
    Camera,
    CameraOff,
    CheckCircle2,
    Leaf,
    QrCode,
    ShieldCheck,
    Sparkles,
} from 'lucide-react';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Toast } from '@/components/ui/Toast';
import { extractApiErrorMessage } from '@/lib/api-client';
import { formatVND } from '@/lib/utils';
import { orderService } from '@/services/order.service';
import type { QRVerificationResponse } from '@/types/api';

const PARTNER_ROLES = ['STORE_PARTNER', 'ADMIN'];

export default function StoreVerifyQrPage() {
    const [qrToken, setQrToken] = useState('');
    const [scannerActive, setScannerActive] = useState(false);
    const [cameraError, setCameraError] = useState<string | null>(null);
    const [verificationResult, setVerificationResult] = useState<QRVerificationResponse | null>(
        null
    );
    const [verificationError, setVerificationError] = useState<string | null>(null);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(
        null
    );

    const scannerRef = useRef<{ stop: () => Promise<void>; clear: () => void } | null>(null);

    const verifyMutation = useMutation({
        mutationFn: (token: string) => orderService.verifyOrderQr(token),
        onSuccess: (res) => {
            setVerificationError(null);
            setVerificationResult(res);
            setToast({
                message: `Xác thực thành công đơn ${res.order_code}!`,
                type: 'success',
            });
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

        startScanner();

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
            <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="mb-6">
                    <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                        <ShieldCheck className="h-3.5 w-3.5" />
                        Cổng Đối Tác Cửa Hàng • HMAC-SHA256 Anti-Replay
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">
                        Quét & Xác thực Mã QR Giao Món
                    </h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Kiểm tra chữ ký HMAC, chống quét trùng lần 2 và cộng điểm xanh cho khách hàng.
                    </p>
                </div>

                <div className="grid gap-6">
                    {/* Camera Toggle Card */}
                    <Card className="p-5">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                                <h2 className="text-base font-semibold text-gray-900">
                                    Quét bằng Camera thiết bị
                                </h2>
                                <p className="text-xs text-gray-500">
                                    Hướng camera về mã QR trên màn hình khách hàng để xác thực tự động.
                                </p>
                            </div>
                            <Button
                                type="button"
                                variant={scannerActive ? 'danger' : 'outline'}
                                size="sm"
                                onClick={() => {
                                    if (scannerActive) {
                                        stopCameraScanner();
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
                                        Bật Camera quét QR
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
                                    placeholder='{"order_id":"...","nonce":"...","exp":...,"sig":"..."}'
                                    className="w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2.5 font-mono text-xs text-gray-900 placeholder:text-gray-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                                />
                            </div>

                            <div className="flex flex-wrap items-center justify-between gap-3">
                                <span className="text-xs text-gray-500">
                                    Mẹo demo: Dán lại cùng 1 chuỗi QR sau khi xác thực thành công để kiểm chứng cơ chế Anti-Replay.
                                </span>
                                <Button
                                    type="submit"
                                    isLoading={verifyMutation.isPending}
                                >
                                    <ShieldCheck className="h-4 w-4" />
                                    Xác thực & Hoàn tất đơn
                                </Button>
                            </div>
                        </form>
                    </Card>

                    {/* Verification Success Result */}
                    {verificationResult && (
                        <Card className="border-emerald-300 bg-emerald-50/70 p-6">
                            <div className="flex items-start gap-3">
                                <CheckCircle2 className="mt-0.5 h-6 w-6 shrink-0 text-emerald-600" />
                                <div className="flex-1 space-y-2">
                                    <div className="flex flex-wrap items-center gap-2">
                                        <h3 className="text-lg font-bold text-emerald-900">
                                            Giao món thành công!
                                        </h3>
                                        <Badge variant="success">{verificationResult.status}</Badge>
                                    </div>
                                    <p className="text-sm text-emerald-800">
                                        {verificationResult.message}
                                    </p>

                                    <div className="mt-3 grid gap-3 rounded-xl border border-emerald-200 bg-white p-4 text-sm sm:grid-cols-3">
                                        <div>
                                            <p className="text-xs text-gray-500">Mã đơn hàng</p>
                                            <p className="font-mono font-bold text-gray-900">
                                                {verificationResult.order_code}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-gray-500">Green Points đã cộng</p>
                                            <p className="inline-flex items-center gap-1 font-bold text-emerald-700">
                                                <Sparkles className="h-4 w-4" />+
                                                {verificationResult.points_awarded} điểm
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-gray-500">CO₂ tiết kiệm</p>
                                            <p className="inline-flex items-center gap-1 font-bold text-emerald-700">
                                                <Leaf className="h-4 w-4" />
                                                {Number(verificationResult.co2_saved_kg).toFixed(2)} kg
                                            </p>
                                        </div>
                                    </div>

                                    {verificationResult.order && (
                                        <p className="text-xs text-emerald-700">
                                            Số lượng: {verificationResult.order.quantity} suất • Tổng
                                            giá trị: {formatVND(verificationResult.order.total_amount)}
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
                                    <p className="mt-1 text-sm text-red-700">{verificationError}</p>
                                </div>
                            </div>
                        </Card>
                    )}
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
