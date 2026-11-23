'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
    AlertTriangle,
    Clock,
    Flame,
    Minus,
    PackagePlus,
    Plus,
    Store,
} from 'lucide-react';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Toast } from '@/components/ui/Toast';
import { extractApiErrorMessage } from '@/lib/api-client';
import { formatVND } from '@/lib/utils';
import { dishService } from '@/services/dish.service';
import { menuService } from '@/services/menu.service';
import { storeService } from '@/services/store.service';
import type {
    MenuItemResponse,
    StoreDetailResponse,
    SurplusDishResponse,
} from '@/types/api';

const PARTNER_ROLES = ['STORE_PARTNER', 'ADMIN'];

export default function StoreSurplusDishesPage() {
    const [store, setStore] = useState<StoreDetailResponse | null>(null);
    const [storeNotFound, setStoreNotFound] = useState(false);
    const [menuItems, setMenuItems] = useState<MenuItemResponse[]>([]);
    const [activeDishes, setActiveDishes] = useState<SurplusDishResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [publishing, setPublishing] = useState(false);
    const [updatingDishId, setUpdatingDishId] = useState<string | null>(null);
    const [toast, setToast] = useState<{
        message: string;
        type: 'success' | 'error' | 'info';
    } | null>(null);

    // Form publish state
    const [selectedMenuItemId, setSelectedMenuItemId] = useState('');
    const [totalQuantity, setTotalQuantity] = useState('5');
    const [pickupStartTime, setPickupStartTime] = useState('17:00');
    const [pickupEndTime, setPickupEndTime] = useState('21:00');
    const [ruleDiscountStartTime, setRuleDiscountStartTime] = useState('19:30');
    const [overridePrice, setOverridePrice] = useState('');
    const [dietaryNotesText, setDietaryNotesText] = useState('');

    const loadData = useCallback(async () => {
        setLoading(true);
        setStoreNotFound(false);
        try {
            const myStore = await storeService.getMyStore();
            setStore(myStore);
            if (myStore.kyc_status === 'APPROVED') {
                const [items, dishes] = await Promise.all([
                    menuService.getStoreMenuItems(myStore.id),
                    dishService.getActiveStoreDishes(myStore.id),
                ]);
                setMenuItems(items);
                setActiveDishes(dishes);
                if (items.length > 0 && !selectedMenuItemId) {
                    setSelectedMenuItemId(items[0].id);
                }
            }
        } catch (err: unknown) {
            const status = (err as { response?: { status?: number } })?.response?.status;
            if (status === 404) {
                setStoreNotFound(true);
            } else {
                setToast({
                    message: extractApiErrorMessage(err, 'Không thể tải dữ liệu món dư của quán.'),
                    type: 'error',
                });
            }
        } finally {
            setLoading(false);
        }
    }, [selectedMenuItemId]);

    useEffect(() => {
        void loadData();
    }, [loadData]);

    const selectedMenuItem = menuItems.find((item) => item.id === selectedMenuItemId);

    const handlePublishSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedMenuItemId) {
            setToast({ message: 'Vui lòng chọn một món từ thực đơn gốc.', type: 'error' });
            return;
        }

        const qty = Number(totalQuantity);
        if (Number.isNaN(qty) || qty <= 0) {
            setToast({ message: 'Số lượng mở bán phải lớn hơn 0.', type: 'error' });
            return;
        }

        if (pickupEndTime <= pickupStartTime) {
            setToast({
                message: 'Giờ kết thúc nhận món phải sau giờ bắt đầu nhận món.',
                type: 'error',
            });
            return;
        }

        if (
            ruleDiscountStartTime &&
            (ruleDiscountStartTime < pickupStartTime || ruleDiscountStartTime > pickupEndTime)
        ) {
            setToast({
                message: 'Giờ kích hoạt giảm sâu giờ chót phải nằm trong khung giờ nhận món.',
                type: 'error',
            });
            return;
        }

        setPublishing(true);
        try {
            const created = await dishService.createSurplusDish({
                menu_item_id: selectedMenuItemId,
                total_quantity: qty,
                pickup_start_time: pickupStartTime,
                pickup_end_time: pickupEndTime,
                rule_discount_start_time: ruleDiscountStartTime || null,
                override_discounted_price: overridePrice ? Number(overridePrice) : null,
                dietary_notes: dietaryNotesText
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean),
            });

            setActiveDishes((prev) => [created, ...prev]);
            setOverridePrice('');
            setDietaryNotesText('');
            setToast({
                message: `Đã mở bán ${created.total_quantity} suất "${created.name}" lên Radar!`,
                type: 'success',
            });
        } catch (err: unknown) {
            setToast({
                message: extractApiErrorMessage(err, 'Mở bán món dư thất bại.'),
                type: 'error',
            });
        } finally {
            setPublishing(false);
        }
    };

    const handleAdjustQuantity = async (dish: SurplusDishResponse, nextQuantity: number) => {
        if (nextQuantity < 0) return;
        setUpdatingDishId(dish.id);
        try {
            const res = await dishService.updateDishQuantity(dish.id, nextQuantity);
            setActiveDishes((prev) =>
                prev.map((item) =>
                    item.id === dish.id
                        ? {
                            ...item,
                            remaining_quantity: res.remaining_quantity,
                            status: res.remaining_quantity === 0 ? 'SOLD_OUT' : 'ACTIVE',
                        }
                        : item
                )
            );
            setToast({
                message: `Đã cập nhật tồn kho "${dish.name}": còn ${res.remaining_quantity} suất.`,
                type: 'success',
            });
        } catch (err: unknown) {
            setToast({
                message: extractApiErrorMessage(err, 'Cập nhật tồn kho thất bại.'),
                type: 'error',
            });
        } finally {
            setUpdatingDishId(null);
        }
    };

    return (
        <AuthGuard allowedRoles={PARTNER_ROLES}>
            <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                            <PackagePlus className="h-3.5 w-3.5" />
                            Xả hàng cuối ca • Tự động giảm giá giờ chót
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            Mở bán & Quản lý Tồn kho Món dư
                        </h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Chọn món từ thực đơn gốc để phát lên Radar giải cứu và điều chỉnh số lượng còn lại theo thời gian thực.
                        </p>
                    </div>

                    {store?.kyc_status === 'APPROVED' && (
                        <Link href="/store/menu">
                            <Button variant="outline">← Quản lý Thực đơn gốc</Button>
                        </Link>
                    )}
                </div>

                {loading ? (
                    <div className="space-y-4">
                        <div className="h-44 animate-pulse rounded-xl bg-gray-100" />
                        <div className="h-64 animate-pulse rounded-xl bg-gray-100" />
                    </div>
                ) : storeNotFound || !store ? (
                    <Card className="p-8 text-center">
                        <Store className="mx-auto h-10 w-10 text-emerald-600" />
                        <h2 className="mt-3 text-lg font-bold text-gray-900">
                            Bạn chưa đăng ký thông tin cửa hàng
                        </h2>
                        <div className="mt-5">
                            <Link href="/store/onboard">
                                <Button>Đăng ký Cửa hàng (KYC)</Button>
                            </Link>
                        </div>
                    </Card>
                ) : store.kyc_status !== 'APPROVED' ? (
                    <Card className="border-amber-300 bg-amber-50/70 p-6">
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-amber-600" />
                            <div>
                                <h2 className="text-base font-bold text-amber-900">
                                    Cửa hàng chưa được phê duyệt KYC ({store.kyc_status})
                                </h2>
                                <p className="mt-1 text-sm text-amber-800">
                                    Vui lòng đợi Admin duyệt hồ sơ hoặc kiểm tra lại trạng thái tại trang Hồ sơ KYC.
                                </p>
                            </div>
                        </div>
                    </Card>
                ) : (
                    <div className="grid gap-8 lg:grid-cols-12">
                        {/* Form Đăng Món Dư */}
                        <Card className="h-fit p-6 lg:col-span-5">
                            <h2 className="mb-4 text-base font-bold text-gray-900">
                                Đăng lô món dư mới
                            </h2>

                            {menuItems.length === 0 ? (
                                <div className="rounded-lg border border-dashed border-gray-300 p-5 text-center">
                                    <p className="text-sm text-gray-700">
                                        Thực đơn gốc của quán đang trống.
                                    </p>
                                    <Link href="/store/menu" className="mt-3 inline-block">
                                        <Button size="sm">Tạo món trong Thực đơn gốc trước</Button>
                                    </Link>
                                </div>
                            ) : (
                                <form onSubmit={handlePublishSubmit} className="space-y-4">
                                    <div>
                                        <label className="mb-1 block text-xs font-semibold text-gray-700">
                                            Chọn món từ thực đơn gốc *
                                        </label>
                                        <select
                                            value={selectedMenuItemId}
                                            onChange={(e) => setSelectedMenuItemId(e.target.value)}
                                            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                        >
                                            {menuItems.map((item) => (
                                                <option key={item.id} value={item.id}>
                                                    {item.name} ({formatVND(item.original_price)})
                                                </option>
                                            ))}
                                        </select>
                                        {selectedMenuItem && (
                                            <p className="mt-1.5 text-xs text-emerald-700">
                                                Giá gốc: {formatVND(selectedMenuItem.original_price)} • Giá giải cứu dự kiến (-50%):{' '}
                                                <strong>
                                                    {formatVND(Number(selectedMenuItem.original_price) * 0.5)}
                                                </strong>
                                            </p>
                                        )}
                                    </div>

                                    <div>
                                        <label className="mb-1 block text-xs font-semibold text-gray-700">
                                            Số lượng suất mở bán *
                                        </label>
                                        <input
                                            type="number"
                                            required
                                            min={1}
                                            max={200}
                                            value={totalQuantity}
                                            onChange={(e) => setTotalQuantity(e.target.value)}
                                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="mb-1 block text-xs font-semibold text-gray-700">
                                                Giờ bắt đầu nhận *
                                            </label>
                                            <input
                                                type="time"
                                                required
                                                value={pickupStartTime}
                                                onChange={(e) => setPickupStartTime(e.target.value)}
                                                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                            />
                                        </div>

                                        <div>
                                            <label className="mb-1 block text-xs font-semibold text-gray-700">
                                                Giờ kết thúc nhận *
                                            </label>
                                            <input
                                                type="time"
                                                required
                                                value={pickupEndTime}
                                                onChange={(e) => setPickupEndTime(e.target.value)}
                                                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                            />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="mb-1 block text-xs font-semibold text-gray-700">
                                                Giờ kích hoạt giảm sâu (-70%)
                                            </label>
                                            <input
                                                type="time"
                                                value={ruleDiscountStartTime}
                                                onChange={(e) => setRuleDiscountStartTime(e.target.value)}
                                                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                            />
                                        </div>

                                        <div>
                                            <label className="mb-1 block text-xs font-semibold text-gray-700">
                                                Giá xả tùy chỉnh (VNĐ)
                                            </label>
                                            <input
                                                type="number"
                                                min={1000}
                                                step={500}
                                                value={overridePrice}
                                                onChange={(e) => setOverridePrice(e.target.value)}
                                                placeholder="Tự động nếu trống"
                                                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="mb-1 block text-xs font-semibold text-gray-700">
                                            Ghi chú khẩu vị lô này (tùy chọn)
                                        </label>
                                        <input
                                            type="text"
                                            value={dietaryNotesText}
                                            onChange={(e) => setDietaryNotesText(e.target.value)}
                                            placeholder="Ví dụ: Ít cay, Đóng hộp giấy"
                                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                                        />
                                    </div>

                                    <Button type="submit" className="w-full" isLoading={publishing}>
                                        <PackagePlus className="h-4 w-4" />
                                        Phát lên Radar Giải Cứu
                                    </Button>
                                </form>
                            )}
                        </Card>

                        {/* Danh sách Món Dư Đang Mở Bán */}
                        <div className="space-y-4 lg:col-span-7">
                            <h2 className="text-base font-bold text-gray-900">
                                Món dư đang hiển thị trên Radar ({activeDishes.length})
                            </h2>

                            {activeDishes.length === 0 ? (
                                <Card className="border-dashed p-10 text-center">
                                    <p className="text-sm font-medium text-gray-700">
                                        Hiện chưa có lô món dư nào đang mở bán.
                                    </p>
                                    <p className="mt-1 text-xs text-gray-500">
                                        Hãy chọn món bên trái để khách hàng quanh bán kính 1–10km nhìn thấy ưu đãi.
                                    </p>
                                </Card>
                            ) : (
                                <div className="space-y-3">
                                    {activeDishes.map((dish) => {
                                        const displayPrice =
                                            dish.current_price ?? dish.rescue_price;
                                        const isUpdating = updatingDishId === dish.id;

                                        return (
                                            <Card key={dish.id} className="p-4">
                                                <div className="flex flex-wrap items-center justify-between gap-4">
                                                    <div className="space-y-1">
                                                        <div className="flex flex-wrap items-center gap-2">
                                                            <h3 className="font-bold text-gray-900">
                                                                {dish.name}
                                                            </h3>
                                                            <Badge
                                                                variant={
                                                                    dish.remaining_quantity > 0
                                                                        ? 'success'
                                                                        : 'neutral'
                                                                }
                                                            >
                                                                {dish.remaining_quantity > 0
                                                                    ? 'ĐANG MỞ BÁN'
                                                                    : 'HẾT SUẤT'}
                                                            </Badge>
                                                            {dish.is_rule_discount_active && (
                                                                <Badge variant="warning">
                                                                    <Flame className="mr-1 inline h-3 w-3" />
                                                                    Giảm giờ chót
                                                                </Badge>
                                                            )}
                                                        </div>

                                                        <div className="flex items-baseline gap-2 text-sm">
                                                            <span className="font-bold text-emerald-700">
                                                                {formatVND(displayPrice)}
                                                            </span>
                                                            <span className="text-xs text-gray-400 line-through">
                                                                {formatVND(dish.original_price)}
                                                            </span>
                                                        </div>

                                                        <p className="flex items-center gap-1.5 text-xs text-gray-500">
                                                            <Clock className="h-3.5 w-3.5" />
                                                            Nhận món: {dish.pickup_start_time.slice(0, 5)} –{' '}
                                                            {dish.pickup_end_time.slice(0, 5)}
                                                        </p>
                                                    </div>

                                                    {/* Điều chỉnh tồn kho nhanh */}
                                                    <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2">
                                                        <span className="text-xs font-medium text-gray-600">
                                                            Còn lại:
                                                        </span>
                                                        <button
                                                            type="button"
                                                            disabled={
                                                                isUpdating ||
                                                                dish.remaining_quantity <= 0
                                                            }
                                                            onClick={() =>
                                                                void handleAdjustQuantity(
                                                                    dish,
                                                                    dish.remaining_quantity - 1
                                                                )
                                                            }
                                                            className="rounded-lg border border-gray-300 bg-white p-1.5 text-gray-700 hover:bg-gray-100 disabled:opacity-40"
                                                        >
                                                            <Minus className="h-3.5 w-3.5" />
                                                        </button>

                                                        <span className="min-w-[48px] text-center font-mono text-sm font-bold text-gray-900">
                                                            {dish.remaining_quantity}/{dish.total_quantity}
                                                        </span>

                                                        <button
                                                            type="button"
                                                            disabled={
                                                                isUpdating ||
                                                                dish.remaining_quantity >=
                                                                dish.total_quantity
                                                            }
                                                            onClick={() =>
                                                                void handleAdjustQuantity(
                                                                    dish,
                                                                    dish.remaining_quantity + 1
                                                                )
                                                            }
                                                            className="rounded-lg border border-gray-300 bg-white p-1.5 text-gray-700 hover:bg-gray-100 disabled:opacity-40"
                                                        >
                                                            <Plus className="h-3.5 w-3.5" />
                                                        </button>
                                                    </div>
                                                </div>
                                            </Card>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
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