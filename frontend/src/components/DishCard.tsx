/* eslint-disable @next/next/no-img-element */
'use client';

import React from 'react';
import { CountdownTimer } from './CountdownTimer';

export interface RescueDishItem {
    id: string;
    name: string;
    storeName: string;
    storeAddress: string;
    distanceText: string;
    originalPrice: number;
    discountedPrice: number;
    discountPercent: number;
    remainingQuantity: number;
    tagCaption: string;
    countdownSeconds: number;
    imageUrl: string;
    category: 'RICE' | 'NOODLES' | 'BAKERY' | 'VEGETARIAN';
    lat: number;
    lng: number;
}

interface DishCardProps {
    dish: RescueDishItem;
    isSelected?: boolean;
    onSelectDish?: (dish: RescueDishItem) => void;
    onRescueClick: (dish: RescueDishItem) => void;
}

export function DishCard({
    dish,
    isSelected = false,
    onSelectDish,
    onRescueClick,
}: DishCardProps) {
    const formatVnd = (amount: number) =>
        amount.toLocaleString('vi-VN') + 'đ';

    return (
        <div
            onClick={() => onSelectDish?.(dish)}
            className={`flex cursor-pointer flex-col gap-4 rounded-2xl border bg-white p-4 transition sm:flex-row sm:items-center ${isSelected
                    ? 'border-[#10B981] ring-2 ring-[#10B981]/20'
                    : 'border-gray-100 shadow-sm hover:border-[#10B981]/50'
                }`}
        >
            {/* Cột ảnh + Badge giảm giá + Caption */}
            <div className="flex flex-col items-center sm:w-28 shrink-0">
                <div className="relative h-24 w-full overflow-hidden rounded-xl bg-gray-100 sm:h-24 sm:w-28">
                    <img
                        src={dish.imageUrl}
                        alt={dish.name}
                        className="h-full w-full object-cover"
                    />
                    <span className="absolute left-2 top-2 rounded-md bg-[#F97316] px-2 py-0.5 text-[11px] font-bold text-white shadow-sm">
                        -{dish.discountPercent}%
                    </span>
                </div>
                <span className="mt-1.5 text-[11px] text-gray-500">
                    {dish.tagCaption}
                </span>
            </div>

            {/* Cột thông tin món ăn */}
            <div className="flex flex-1 flex-col justify-between space-y-2">
                <div className="flex items-start justify-between gap-2">
                    <h3 className="text-base font-bold text-gray-900">{dish.name}</h3>
                    <span className="shrink-0 rounded-full bg-[#E6F7F0] px-2.5 py-0.5 text-[11px] font-semibold text-[#0F8A5F]">
                        Còn {dish.remainingQuantity} suất
                    </span>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                    <span className="truncate">
                        {dish.storeName} • {dish.storeAddress}
                    </span>
                    <span className="shrink-0 font-medium text-gray-600">
                        🚶 {dish.distanceText}
                    </span>
                </div>

                <CountdownTimer initialSeconds={dish.countdownSeconds} />

                <div className="flex items-center justify-between pt-1">
                    <div className="flex items-baseline gap-2">
                        <span className="text-xs text-gray-400 line-through">
                            {formatVnd(dish.originalPrice)}
                        </span>
                        <span className="text-lg font-extrabold text-[#0F8A5F]">
                            {formatVnd(dish.discountedPrice)}
                        </span>
                    </div>

                    <button
                        type="button"
                        onClick={(e) => {
                            e.stopPropagation();
                            onRescueClick(dish);
                        }}
                        className="rounded-xl bg-[#10B981] px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-[#0D9668]"
                    >
                        Cứu món ngay
                    </button>
                </div>
            </div>
        </div>
    );
}

export default DishCard;