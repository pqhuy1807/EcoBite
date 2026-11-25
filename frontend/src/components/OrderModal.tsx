/* eslint-disable @next/next/no-img-element */
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { RescueDishItem } from './DishCard';
import { extractApiErrorMessage } from '@/lib/api-client';
import { orderService } from '@/services/order.service';
import { paymentService } from '@/services/payment.service';
import type { PaymentMethod } from '@/types/api';

interface OrderModalProps {
    dish: RescueDishItem | null;
    onClose: () => void;
    onOrderSuccess?: (dishId: string, quantityBought: number) => void;
}

interface CreatedOrderSummary {
    order_id?: string;
    order_code: string;
    co2_saved_kg: number;
    green_points: number;
    payment_method: PaymentMethod;
    vnpay_warning?: string;
}

export function OrderModal({
    dish,
    onClose,
    onOrderSuccess,
}: OrderModalProps) {
    const [quantity, setQuantity] = useState(1);
    const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('COD');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isOutOfStockError, setIsOutOfStockError] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [createdOrder, setCreatedOrder] =
        useState<CreatedOrderSummary | null>(null);

    if (!dish) return null;

    const maxQty = dish.remainingQuantity;
    const totalPrice = dish.discountedPrice * quantity;
    const co2Saved = Number((quantity * 2.5).toFixed(1));
    const greenPoints = quantity * 25;

    const formatVnd = (amount: number) =>
        amount.toLocaleString('vi-VN') + 'đ';

    const handleConfirmOrder = async () => {
        if (quantity > maxQty || maxQty <= 0) {
            setIsOutOfStockError(true);
            return;
        }

        setIsSubmitting(true);
        setErrorMessage(null);
        try {
            const res = await orderService.createRescueOrder({
                dish_id: dish.id,
                quantity,
                payment_method: paymentMethod,
            });

            onOrderSuccess?.(dish.id, quantity);

            if (paymentMethod === 'VNPAY' && res.id) {
                try {
                    const vnpay = await paymentService.createVnpayUrl(res.id);
                    window.location.href = vnpay.payment_url;
                    return;
                } catch (vnpayErr: unknown) {
                    setCreatedOrder({
                        order_id: res.id,
                        order_code: res.order_code,
                        co2_saved_kg: Number(res.co2_saved_kg ?? co2Saved),
                        green_points: Number(res.green_points_earned ?? greenPoints),
                        payment_method: paymentMethod,
                        vnpay_warning: extractApiErrorMessage(
                            vnpayErr,
                            'Đơn hàng đã được tạo nhưng chưa mở được cổng VNPay. Bạn có thể bấm Thanh toán VNPay tại mục Đơn của tôi.'
                        ),
                    });
                    return;
                }
            }

            setCreatedOrder({
                order_id: res.id,
                order_code: res.order_code,
                co2_saved_kg: Number(res.co2_saved_kg ?? co2Saved),
                green_points: Number(res.green_points_earned ?? greenPoints),
                payment_method: paymentMethod,
            });
        } catch (err: unknown) {
            const status = (err as { response?: { status?: number } })?.response
                ?.status;
            if (status === 409) {
                setIsOutOfStockError(true);
            } else if (status === 401 || status === 403) {
                setErrorMessage(
                    extractApiErrorMessage(
                        err,
                        'Vui lòng đăng nhập bằng tài khoản Người giải cứu (CONSUMER) để đặt đơn.'
                    )
                );
            } else {
                setErrorMessage(
                    extractApiErrorMessage(
                        err,
                        'Không thể tạo đơn hàng lúc này. Vui lòng kiểm tra kết nối máy chủ.'
                    )
                );
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isOutOfStockError) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-2xl">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#FEE2E2] text-2xl text-[#DC2626]">
                        ❗
                    </div>
                    <h3 className="text-xl font-bold text-gray-900">
                        Rất tiếc, món ăn vừa hết suất!
                    </h3>
                    <p className="mt-2.5 text-sm leading-relaxed text-gray-600">
                        Số lượng suất ăn giải cứu tại quán vừa được người dùng khác đặt hết.
                        Vui lòng chọn món khác gần bạn.
                    </p>
                    <button
                        type="button"
                        onClick={onClose}
                        className="mt-6 w-full rounded-xl bg-[#0F8A5F] py-3 text-sm font-semibold text-white transition hover:bg-[#0B6E4B]"
                    >
                        Tìm món khác quanh đây
                    </button>
                </div>
            </div>
        );
    }

    if (createdOrder) {
        const orderUrl = createdOrder.order_id
            ? `/orders?highlight=${createdOrder.order_id}`
            : '/orders';

        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-2xl">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#E6F7F0] text-2xl text-[#10B981]">
                        🎉
                    </div>
                    <h3 className="text-xl font-bold text-gray-900">
                        Đặt đơn giải cứu thành công!
                    </h3>
                    <p className="mt-2 text-xs text-gray-500">
                        Vui lòng xuất trình mã QR của đơn hàng dưới đây khi đến nhận món tại{' '}
                        {dish.storeName}
                    </p>

                    <div className="my-5 rounded-xl border border-dashed border-[#10B981] bg-[#F4FBF7] p-4">
                        <span className="block text-xs text-gray-500">Mã đơn hàng</span>
                        <span className="mt-1 block text-lg font-extrabold tracking-wider text-[#0F8A5F]">
                            {createdOrder.order_code}
                        </span>
                    </div>

                    {createdOrder.vnpay_warning && (
                        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
                            {createdOrder.vnpay_warning}
                        </div>
                    )}

                    <div className="mb-6 rounded-xl bg-[#E6F7F0] p-3 text-xs font-semibold text-[#0F8A5F]">
                        🌱 Bạn sẽ giúp Trái Đất giảm {createdOrder.co2_saved_kg} kg CO₂e và
                        nhận +{createdOrder.green_points} Green Points khi hoàn tất nhận món!
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="rounded-xl border border-gray-200 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50"
                        >
                            Đóng
                        </button>
                        <Link
                            href={orderUrl}
                            onClick={onClose}
                            className="rounded-xl bg-[#10B981] py-3 text-center text-sm font-semibold text-white transition hover:bg-[#0D9668]"
                        >
                            Xem đơn &amp; Mã QR
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
                <div className="flex items-center justify-between pb-4">
                    <h3 className="text-lg font-bold text-gray-900">
                        Xác nhận cứu trợ món ăn
                    </h3>
                    <button
                        type="button"
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        ✕
                    </button>
                </div>

                <div className="flex items-center gap-3.5 rounded-xl border border-gray-100 bg-gray-50/70 p-3">
                    <img
                        src={dish.imageUrl}
                        alt={dish.name}
                        className="h-16 w-16 rounded-lg object-cover"
                    />
                    <div className="flex-1">
                        <h4 className="text-sm font-bold text-gray-900">{dish.name}</h4>
                        <p className="text-xs text-gray-500">{dish.storeName}</p>
                        <div className="mt-1 flex items-center justify-between">
                            <span className="text-xs font-bold text-[#0F8A5F]">
                                {formatVnd(dish.discountedPrice)} / suất
                            </span>
                            <span className="rounded-md bg-[#E6F7F0] px-2 py-0.5 text-[10px] font-semibold text-[#0F8A5F]">
                                Còn lại: {dish.remainingQuantity} suất
                            </span>
                        </div>
                    </div>
                </div>

                <div className="mt-5 flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-700">
                        Số lượng suất muốn cứu
                    </span>
                    <div className="flex items-center gap-3 rounded-lg border border-gray-200 px-2.5 py-1">
                        <button
                            type="button"
                            onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                            className="px-1.5 text-sm font-bold text-gray-500 hover:text-gray-800"
                        >
                            −
                        </button>
                        <span className="min-w-[20px] text-center text-xs font-bold text-gray-900">
                            {quantity}
                        </span>
                        <button
                            type="button"
                            onClick={() => setQuantity((q) => Math.min(maxQty, q + 1))}
                            className="px-1.5 text-sm font-bold text-[#10B981] hover:text-[#0F8A5F]"
                        >
                            +
                        </button>
                    </div>
                </div>

                <div className="mt-4">
                    <span className="mb-2 block text-xs font-medium text-gray-700">
                        Phương thức thanh toán
                    </span>
                    <div className="grid grid-cols-2 gap-2.5">
                        <button
                            type="button"
                            onClick={() => setPaymentMethod('COD')}
                            className={`rounded-xl border px-3 py-2.5 text-left text-xs transition ${paymentMethod === 'COD'
                                    ? 'border-[#10B981] bg-[#E6F7F0] font-semibold text-[#0F8A5F]'
                                    : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                                }`}
                        >
                            <span className="block font-bold">Tiền mặt (COD)</span>
                            <span className="text-[11px] opacity-80">Trả trực tiếp tại quán</span>
                        </button>
                        <button
                            type="button"
                            onClick={() => setPaymentMethod('VNPAY')}
                            className={`rounded-xl border px-3 py-2.5 text-left text-xs transition ${paymentMethod === 'VNPAY'
                                    ? 'border-blue-600 bg-blue-50 font-semibold text-blue-800'
                                    : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                                }`}
                        >
                            <span className="block font-bold">VNPay Sandbox</span>
                            <span className="text-[11px] opacity-80">Thanh toán trực tuyến</span>
                        </button>
                    </div>
                </div>

                {errorMessage && (
                    <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700">
                        {errorMessage}
                    </div>
                )}

                <div className="mt-4 flex items-center gap-2.5 rounded-xl bg-[#E6F7F0] p-3 text-xs text-[#0F8A5F]">
                    <span className="text-base">🌱</span>
                    <span>
                        Bạn sẽ giúp giảm <strong>{co2Saved} kg CO₂e</strong> và nhận{' '}
                        <strong>+{greenPoints} Green Points</strong>
                    </span>
                </div>

                <div className="mt-5 flex items-center justify-between border-t border-gray-100 pt-4">
                    <span className="text-xs font-medium text-gray-600">
                        Tổng thanh toán:
                    </span>
                    <span className="text-lg font-extrabold text-gray-900">
                        {formatVnd(totalPrice)}
                    </span>
                </div>

                <div className="mt-5 grid grid-cols-3 gap-3">
                    <button
                        type="button"
                        onClick={onClose}
                        className="col-span-1 rounded-xl border border-gray-200 py-2.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                    >
                        Hủy
                    </button>
                    <button
                        type="button"
                        disabled={isSubmitting}
                        onClick={() => void handleConfirmOrder()}
                        className="col-span-2 rounded-xl bg-[#10B981] py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-[#0D9668] disabled:opacity-50"
                    >
                        {isSubmitting
                            ? 'Đang xử lý...'
                            : paymentMethod === 'VNPAY'
                                ? 'Đặt & Thanh toán VNPay'
                                : 'Xác nhận cứu món'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default OrderModal;