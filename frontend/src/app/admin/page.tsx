'use client';

import { useCallback, useEffect, useState } from 'react';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { storeService } from '@/services/store.service';
import type { StoreDetailResponse } from '@/types/api';

const ADMIN_ALLOWED_ROLES = ['ADMIN'];

function getErrorMessage(error: unknown, fallback: string): string {
    if (
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail ===
        'string'
    ) {
        return (error as { response: { data: { detail: string } } }).response.data.detail;
    }
    if (error instanceof Error && error.message) {
        return error.message;
    }
    return fallback;
}

function AdminKycContent() {
    const [stores, setStores] = useState<StoreDetailResponse[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(
        null
    );

    const [rejectingId, setRejectingId] = useState<string | null>(null);
    const [rejectReason, setRejectReason] = useState<string>('');
    const [submittingId, setSubmittingId] = useState<string | null>(null);

    const fetchPendingStores = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const items = await storeService.getPendingStores();
            setStores(items);
        } catch (err: unknown) {
            setError(getErrorMessage(err, 'Không thể tải danh sách cửa hàng chờ duyệt KYC.'));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void fetchPendingStores();
    }, [fetchPendingStores]);

    const handleApprove = async (store: StoreDetailResponse) => {
        setSubmittingId(store.id);
        setFeedback(null);
        try {
            await storeService.reviewStoreKyc(store.id, 'APPROVED');
            setStores((prev) => prev.filter((item) => item.id !== store.id));
            if (rejectingId === store.id) {
                setRejectingId(null);
                setRejectReason('');
            }
            setFeedback({
                type: 'success',
                text: `Đã phê duyệt cửa hàng "${store.name}" (APPROVED).`,
            });
        } catch (err: unknown) {
            setFeedback({
                type: 'error',
                text: getErrorMessage(err, `Phê duyệt cửa hàng "${store.name}" thất bại.`),
            });
        } finally {
            setSubmittingId(null);
        }
    };

    const openRejectForm = (storeId: string) => {
        setRejectingId(storeId);
        setRejectReason('');
        setFeedback(null);
    };

    const cancelRejectForm = () => {
        setRejectingId(null);
        setRejectReason('');
    };

    const handleConfirmReject = async (store: StoreDetailResponse) => {
        const trimmedReason = rejectReason.trim();
        if (!trimmedReason) return;

        setSubmittingId(store.id);
        setFeedback(null);
        try {
            await storeService.reviewStoreKyc(store.id, 'REJECTED', trimmedReason);
            setStores((prev) => prev.filter((item) => item.id !== store.id));
            setRejectingId(null);
            setRejectReason('');
            setFeedback({
                type: 'success',
                text: `Đã từ chối hồ sơ "${store.name}" (REJECTED).`,
            });
        } catch (err: unknown) {
            setFeedback({
                type: 'error',
                text: getErrorMessage(err, `Từ chối cửa hàng "${store.name}" thất bại.`),
            });
        } finally {
            setSubmittingId(null);
        }
    };

    return (
        <main className="mx-auto max-w-5xl px-4 py-8">
            <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">
                        Kiểm duyệt Đối tác Cửa hàng (KYC)
                    </h1>
                    <p className="mt-1 text-sm text-gray-600">
                        Xác minh thông tin địa điểm và giấy chứng nhận An toàn vệ sinh thực phẩm (ATVSTP).
                    </p>
                </div>

                <button
                    type="button"
                    onClick={() => void fetchPendingStores()}
                    disabled={loading}
                    className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                    {loading ? 'Đang tải...' : 'Làm mới danh sách'}
                </button>
            </div>

            {feedback && (
                <div
                    className={`mb-6 rounded-lg border px-4 py-3 text-sm ${feedback.type === 'success'
                        ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                        : 'border-red-200 bg-red-50 text-red-800'
                        }`}
                >
                    {feedback.text}
                </div>
            )}

            {error && (
                <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    <p className="font-medium">{error}</p>
                    <button
                        type="button"
                        onClick={() => void fetchPendingStores()}
                        className="mt-2 font-semibold underline hover:text-red-900"
                    >
                        Thử lại
                    </button>
                </div>
            )}

            {loading ? (
                <div className="space-y-4">
                    {[1, 2].map((skeleton) => (
                        <div
                            key={skeleton}
                            className="h-36 animate-pulse rounded-xl border border-gray-200 bg-gray-100"
                        />
                    ))}
                </div>
            ) : stores.length === 0 ? (
                <div className="rounded-xl border border-dashed border-gray-300 bg-white p-12 text-center">
                    <p className="text-base font-medium text-gray-800">
                        Không có hồ sơ cửa hàng nào đang chờ duyệt
                    </p>
                    <p className="mt-1 text-sm text-gray-500">
                        Tất cả yêu cầu đăng ký đối tác mới sẽ hiển thị tại đây.
                    </p>
                </div>
            ) : (
                <div className="space-y-4">
                    {stores.map((store) => {
                        const isSubmitting = submittingId === store.id;
                        const isRejecting = rejectingId === store.id;

                        return (
                            <section
                                key={store.id}
                                className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
                            >
                                <div className="flex flex-wrap items-start justify-between gap-4">
                                    <div className="space-y-1.5">
                                        <div className="flex items-center gap-2.5">
                                            <h2 className="text-lg font-semibold text-gray-900">{store.name}</h2>
                                            <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
                                                {store.kyc_status}
                                            </span>
                                        </div>

                                        <p className="text-sm text-gray-700">
                                            <span className="font-medium">Địa chỉ:</span> {store.address}
                                        </p>

                                        {store.phone && (
                                            <p className="text-sm text-gray-700">
                                                <span className="font-medium">Số điện thoại:</span> {store.phone}
                                            </p>
                                        )}

                                        {store.description && (
                                            <p className="text-sm text-gray-600">{store.description}</p>
                                        )}

                                        <div className="pt-1">
                                            {store.kyc_license_url ? (
                                                <a
                                                    href={store.kyc_license_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-700 underline hover:text-emerald-900"
                                                >
                                                    Xem giấy chứng nhận ATVSTP ↗
                                                </a>
                                            ) : (
                                                <span className="text-sm italic text-red-600">
                                                    Chưa đính kèm liên kết giấy chứng nhận ATVSTP
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2.5">
                                        <button
                                            type="button"
                                            disabled={isSubmitting}
                                            onClick={() => void handleApprove(store)}
                                            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                                        >
                                            {isSubmitting && !isRejecting ? 'Đang xử lý...' : 'Phê duyệt (APPROVED)'}
                                        </button>

                                        <button
                                            type="button"
                                            disabled={isSubmitting || isRejecting}
                                            onClick={() => openRejectForm(store.id)}
                                            className="rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50"
                                        >
                                            Từ chối
                                        </button>
                                    </div>
                                </div>

                                {isRejecting && (
                                    <div className="mt-4 rounded-lg border border-red-200 bg-red-50/70 p-4">
                                        <label
                                            htmlFor={`reject-reason-${store.id}`}
                                            className="block text-sm font-medium text-red-900"
                                        >
                                            Lý do từ chối hồ sơ <span className="text-red-600">*</span>
                                        </label>
                                        <textarea
                                            id={`reject-reason-${store.id}`}
                                            rows={2}
                                            value={rejectReason}
                                            onChange={(e) => setRejectReason(e.target.value)}
                                            placeholder="Ví dụ: Ảnh giấy chứng nhận ATVSTP bị mờ hoặc đã hết hạn..."
                                            className="mt-1.5 w-full rounded-lg border border-red-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-red-500 focus:outline-none"
                                        />
                                        <div className="mt-3 flex justify-end gap-2">
                                            <button
                                                type="button"
                                                disabled={isSubmitting}
                                                onClick={cancelRejectForm}
                                                className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                                            >
                                                Hủy
                                            </button>
                                            <button
                                                type="button"
                                                disabled={isSubmitting || !rejectReason.trim()}
                                                onClick={() => void handleConfirmReject(store)}
                                                className="rounded-lg bg-red-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                                            >
                                                {isSubmitting ? 'Đang gửi...' : 'Xác nhận từ chối (REJECTED)'}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </section>
                        );
                    })}
                </div>
            )}
        </main>
    );
}

export default function AdminKycPage() {
    return (
        <AuthGuard allowedRoles={ADMIN_ALLOWED_ROLES}>
            <AdminKycContent />
        </AuthGuard>
    );
}