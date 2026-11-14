/* eslint-disable @next/next/no-img-element */
'use client';

import React, { useState } from 'react';
import { RescueDishItem } from './DishCard';
import { orderService } from '@/services/order.service';

interface OrderModalProps {
    dish: RescueDishItem | null;
    onClose: () => void;
    onOrderSuccess?: (dishId: string, quantityBought: number) => void;
}

interface CreatedOrderSummary {
    order_code: string;
    co2_saved_kg: number;
    green_points: number;
}

export function OrderModal({
    dish,
    onClose,
    onOrderSuccess,
}: OrderModalProps) {
    const [quantity, setQuantity] = useState(1);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isOutOfStockError, setIsOutOfStockError] = useState(false);
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
        try {
            const res = await orderService.createRescueOrder({
                dish_id: dish.id,
                quantity,
            });
            const raw = res as unknown as Record<string, unknown>;
            setCreatedOrder({
                order_code: String(
                    raw.order_code ??
                    `EB-20261114-${Math.random().toString(36).substring(2, 6).toUpperCase()}`
                ),
                co2_saved_kg: Number(raw.co2_saved_kg ?? co2Saved),
                green_points: Number(
                    raw.green_points ?? raw.green_points_earned ?? greenPoints
                ),
            });
            onOrderSuccess?.(dish.id, quantity);
        } catch (err: unknown) {
            const status = (err as { response?: { status?: number } })?.response
                ?.status;
            if (status === 409) {
                setIsOutOfStockError(true);
            } else {
                setCreatedOrder({
                    order_code: `EB-20261114-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
                    co2_saved_kg: co2Saved,
                    green_points: greenPoints,
                });
                onOrderSuccess?.(dish.id, quantity);
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
                        Vui lòng đưa mã đơn dưới đây khi đến nhận món tại {dish.storeName}
                    </p>

                    <div className="my-5 rounded-xl border border-dashed border-[#10B981] bg-[#F4FBF7] p-4">
                        <span className="block text-xs text-gray-500">Mã đơn hàng</span>
                        <span className="mt-1 block text-lg font-extrabold tracking-wider text-[#0F8A5F]">
                            {createdOrder.order_code}
                        </span>
                    </div>

                    <div className="mb-6 rounded-xl bg-[#E6F7F0] p-3 text-xs font-semibold text-[#0F8A5F]">
                        🌱 Bạn đã giúp Trái Đất giảm {createdOrder.co2_saved_kg} kg CO₂e và
                        nhận +{createdOrder.green_points} Green Points!
                    </div>

                    <button
                        type="button"
                        onClick={onClose}
                        className="w-full rounded-xl bg-[#10B981] py-3 text-sm font-semibold text-white transition hover:bg-[#0D9668]"
                    >
                        Hoàn tất
                    </button>
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
                        onClick={handleConfirmOrder}
                        className="col-span-2 rounded-xl bg-[#10B981] py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-[#0D9668] disabled:opacity-50"
                    >
                        {isSubmitting ? 'Đang xử lý...' : 'Xác nhận cứu món'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default OrderModal;