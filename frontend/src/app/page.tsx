'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
    AlertTriangle,
    Clock,
    Compass,
    Leaf,
    MapPin,
    Navigation,
    QrCode,
    RefreshCw,
    ShoppingBag,
    Sparkles,
    Star,
} from 'lucide-react';
import { DynamicRadarMap } from '@/components/radar/DynamicRadarMap';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Toast } from '@/components/ui/Toast';
import { useGeolocation } from '@/hooks/useGeolocation';
import { extractApiErrorMessage } from '@/lib/api-client';
import { formatDistance, formatVND } from '@/lib/utils';
import { discoveryService } from '@/services/discovery.service';
import { orderService } from '@/services/order.service';
import type {
    DishAllergenNote,
    FoodCategory,
    NearbyDishItem,
    NearbyStore,
    OrderResponse,
    PaymentMethod,
    User,
} from '@/types/api';

const CATEGORIES: Array<{ key: 'ALL' | FoodCategory; label: string }> = [
    { key: 'ALL', label: 'Tất cả' },
    { key: 'RICE', label: 'Cơm' },
    { key: 'NOODLES', label: 'Bún / Phở' },
    { key: 'BAKERY', label: 'Bánh mì / Bánh ngọt' },
    { key: 'VEGETARIAN', label: 'Món chay' },
    { key: 'DRINKS', label: 'Đồ uống' },
    { key: 'OTHER', label: 'Khác' },
] as const;

const DEMO_LOCATIONS = [
    { label: 'Quận 1 (Bến Thành)', lat: 10.7769, lng: 106.7009 },
    { label: 'Quận 3 (Võ Văn Tần)', lat: 10.7758, lng: 106.6881 },
    { label: 'Bình Thạnh (Hàng Xanh)', lat: 10.8019, lng: 106.7115 },
];

function renderAllergenLabel(item: string | DishAllergenNote): string {
    if (typeof item === 'string') return item;
    return item.allergen;
}

export default function HomePage() {
    const router = useRouter();
    const queryClient = useQueryClient();
    const {
        coords: gpsCoords,
        isLoading: gpsLoading,
        error: gpsError,
        isFallback: gpsFallback,
        refreshLocation,
    } = useGeolocation();

    const [manualCoords, setManualCoords] = useState<{ lat: number; lng: number } | null>(null);
    const [radiusKm, setRadiusKm] = useState<number>(5);
    const [category, setCategory] = useState<'ALL' | FoodCategory>('ALL');
    const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);

    const [currentUser, setCurrentUser] = useState<User | null>(null);
    const [activeDish, setActiveDish] = useState<{ store: NearbyStore; dish: NearbyDishItem } | null>(
        null
    );
    const [quantity, setQuantity] = useState<number>(1);
    const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('COD');
    const [orderError, setOrderError] = useState<string | null>(null);
    const [createdOrder, setCreatedOrder] = useState<OrderResponse | null>(null);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(
        null
    );

    useEffect(() => {
        const readUser = () => {
            try {
                const raw = localStorage.getItem('user');
                setCurrentUser(raw ? (JSON.parse(raw) as User) : null);
            } catch {
                setCurrentUser(null);
            }
        };
        readUser();
        window.addEventListener('ecobite-auth-change', readUser);
        window.addEventListener('storage', readUser);
        return () => {
            window.removeEventListener('ecobite-auth-change', readUser);
            window.removeEventListener('storage', readUser);
        };
    }, []);

    const activeCoords = manualCoords ?? gpsCoords;

    const {
        data: nearbyData,
        isLoading: storesLoading,
        isFetching: storesFetching,
        error: storesError,
        refetch,
    } = useQuery({
        queryKey: ['nearby-stores', activeCoords.lat, activeCoords.lng, radiusKm, category],
        queryFn: () =>
            discoveryService.getNearbyStores({
                lat: activeCoords.lat,
                lng: activeCoords.lng,
                radius_km: radiusKm,
                category: category === 'ALL' ? undefined : category,
            }),
    });

    const createOrderMutation = useMutation({
        mutationFn: orderService.createRescueOrder,
        onSuccess: (order) => {
            setOrderError(null);
            setCreatedOrder(order);
            setToast({
                message: `Đặt đơn ${order.order_code} thành công! Bạn đã cứu ${Number(
                    order.co2_saved_kg
                ).toFixed(2)} kg CO₂.`,
                type: 'success',
            });
            queryClient.invalidateQueries({ queryKey: ['nearby-stores'] });
            queryClient.invalidateQueries({ queryKey: ['my-orders'] });
        },
        onError: (err) => {
            const msg = extractApiErrorMessage(
                err,
                'Không thể tạo đơn giải cứu. Vui lòng kiểm tra tồn kho và khung giờ.'
            );
            setOrderError(msg);
            setToast({ message: msg, type: 'error' });
            queryClient.invalidateQueries({ queryKey: ['nearby-stores'] });
        },
    });

    const stores = useMemo(() => nearbyData?.results ?? [], [nearbyData]);

    const openOrderModal = (store: NearbyStore, dish: NearbyDishItem) => {
        setActiveDish({ store, dish });
        setQuantity(1);
        setPaymentMethod('COD');
        setOrderError(null);
        setCreatedOrder(null);
    };

    const closeOrderModal = () => {
        setActiveDish(null);
        setOrderError(null);
        setCreatedOrder(null);
    };

    const handleConfirmOrder = (e: React.FormEvent) => {
        e.preventDefault();
        if (!activeDish) return;
        setOrderError(null);
        createOrderMutation.mutate({
            dish_id: activeDish.dish.id,
            quantity,
            payment_method: paymentMethod,
        });
    };

    const totalDishCount = useMemo(
        () => stores.reduce((acc, s) => acc + s.dishes.length, 0),
        [stores]
    );

    return (
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            {/* Hero & Controls */}
            <section className="mb-6 rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 via-white to-teal-50 p-5 shadow-sm sm:p-6">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                        <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                            <Sparkles className="h-3.5 w-3.5" />
                            Radar Giải Cứu Thực Phẩm Giờ Chót
                        </div>
                        <h1 className="text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl">
                            Khám phá món ngon giảm đến 70% quanh bạn
                        </h1>
                        <p className="mt-1 text-sm text-gray-600">
                            Định vị cửa hàng lân cận, đặt suất ăn chống quá bán và nhận mã QR động tại quầy.
                        </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                        <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => {
                                setManualCoords(null);
                                refreshLocation();
                            }}
                            disabled={gpsLoading}
                        >
                            <Navigation className="h-4 w-4 text-emerald-600" />
                            {gpsLoading ? 'Đang định vị...' : 'Dùng GPS hiện tại'}
                        </Button>
                        {DEMO_LOCATIONS.map((loc) => {
                            const isActive =
                                Math.abs(activeCoords.lat - loc.lat) < 0.0005 &&
                                Math.abs(activeCoords.lng - loc.lng) < 0.0005;
                            return (
                                <button
                                    key={loc.label}
                                    type="button"
                                    onClick={() => setManualCoords({ lat: loc.lat, lng: loc.lng })}
                                    className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                                        isActive
                                            ? 'border-emerald-600 bg-emerald-600 text-white'
                                            : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                                    }`}
                                >
                                    {loc.label}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {gpsError && !manualCoords && (
                    <p className="mt-3 text-xs text-amber-700">
                        {gpsError} {gpsFallback ? '(Đang dùng tọa độ mặc định Quận 1, TP.HCM)' : ''}
                    </p>
                )}

                {/* Radius & Category Filters */}
                <div className="mt-5 grid gap-4 border-t border-emerald-100/80 pt-4 md:grid-cols-12 md:items-center">
                    <div className="md:col-span-4">
                        <div className="mb-1.5 flex items-center justify-between text-sm">
                            <span className="flex items-center gap-1.5 font-medium text-gray-700">
                                <Compass className="h-4 w-4 text-emerald-600" />
                                Bán kính Radar
                            </span>
                            <span className="rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-800">
                                {radiusKm} km
                            </span>
                        </div>
                        <input
                            type="range"
                            min={1}
                            max={10}
                            step={0.5}
                            value={radiusKm}
                            onChange={(e) => setRadiusKm(Number(e.target.value))}
                            className="h-2 w-full cursor-pointer accent-emerald-600"
                            aria-label="Bán kính tìm kiếm km"
                        />
                        <div className="mt-1 flex justify-between text-[11px] text-gray-400">
                            <span>1 km</span>
                            <span>5 km</span>
                            <span>10 km</span>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-2 md:col-span-8 md:justify-end">
                        {CATEGORIES.map((cat) => (
                            <button
                                key={cat.key}
                                type="button"
                                onClick={() => setCategory(cat.key)}
                                className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                                    category === cat.key
                                        ? 'bg-emerald-600 text-white shadow-sm'
                                        : 'border border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                                }`}
                            >
                                {cat.label}
                            </button>
                        ))}
                    </div>
                </div>
            </section>

            {/* Main Grid: Map + Store List */}
            <div className="grid gap-6 lg:grid-cols-12">
                {/* Interactive Radar Map */}
                <div className="lg:col-span-5">
                    <div className="sticky top-20 space-y-3">
                        <div className="flex items-center justify-between">
                            <h2 className="flex items-center gap-2 text-base font-bold text-gray-900">
                                <MapPin className="h-4 w-4 text-emerald-600" />
                                Bản đồ Radar ({stores.length} quán • {totalDishCount} món)
                            </h2>
                            <button
                                type="button"
                                onClick={() => refetch()}
                                className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 hover:text-emerald-800"
                            >
                                <RefreshCw className={`h-3.5 w-3.5 ${storesFetching ? 'animate-spin' : ''}`} />
                                Làm mới
                            </button>
                        </div>

                        <DynamicRadarMap
                            userLocation={activeCoords}
                            radiusKm={radiusKm}
                            stores={stores}
                            selectedStoreId={selectedStoreId}
                            onSelectStore={(id) => setSelectedStoreId(id)}
                        />
                    </div>
                </div>

                {/* Store & Dish List */}
                <div className="space-y-4 lg:col-span-7">
                    {storesLoading && (
                        <div className="space-y-4">
                            {[1, 2].map((i) => (
                                <Card key={i} className="h-48 animate-pulse bg-gray-100 p-5" />
                            ))}
                        </div>
                    )}

                    {storesError && (
                        <Card className="border-red-200 bg-red-50 p-5 text-sm text-red-700">
                            Không thể tải danh sách cửa hàng gần đây:{' '}
                            {extractApiErrorMessage(storesError, 'Lỗi kết nối máy chủ backend.')}
                        </Card>
                    )}

                    {!storesLoading && !storesError && stores.length === 0 && (
                        <Card className="p-8 text-center">
                            <Compass className="mx-auto mb-3 h-10 w-10 text-gray-300" />
                            <h3 className="text-base font-semibold text-gray-900">
                                Chưa tìm thấy suất ăn giải cứu trong bán kính {radiusKm} km
                            </h3>
                            <p className="mt-1 text-sm text-gray-500">
                                Hãy thử tăng bán kính Radar lên 5–10 km hoặc chọn danh mục &ldquo;Tất cả&rdquo;.
                            </p>
                        </Card>
                    )}

                    {stores.map((store) => {
                        const isSelected = selectedStoreId === store.id;
                        return (
                            <Card
                                key={store.id}
                                className={`overflow-hidden transition-all ${
                                    isSelected
                                        ? 'ring-2 ring-emerald-500 ring-offset-2'
                                        : 'hover:border-emerald-200'
                                }`}
                            >
                                {/* Store Header */}
                                <div
                                    className="flex cursor-pointer flex-wrap items-start justify-between gap-2 border-b border-gray-100 bg-gray-50/60 px-5 py-4"
                                    onClick={() => setSelectedStoreId(store.id)}
                                >
                                    <div>
                                        <div className="flex flex-wrap items-center gap-2">
                                            <h3 className="text-lg font-bold text-gray-900">{store.name}</h3>
                                            <Badge variant="info">
                                                Cách {formatDistance(store.distance_meters)}
                                            </Badge>
                                        </div>
                                        <p className="mt-1 flex items-center gap-1 text-xs text-gray-600">
                                            <MapPin className="h-3.5 w-3.5 text-gray-400" />
                                            {store.address}
                                        </p>
                                    </div>

                                    <div className="flex items-center gap-3 text-xs font-medium">
                                        <span className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-1 text-amber-800">
                                            <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-500" />
                                            {Number(store.rating_avg || 5).toFixed(1)}
                                        </span>
                                        <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-emerald-700">
                                            <Leaf className="h-3.5 w-3.5" />
                                            {Number(store.total_co2_saved_kg || 0).toFixed(1)} kg CO₂
                                        </span>
                                    </div>
                                </div>

                                {/* Dishes */}
                                <div className="divide-y divide-gray-100">
                                    {store.dishes.map((dish) => {
                                        const discountPct =
                                            dish.original_price > 0
                                                ? Math.round(
                                                      ((dish.original_price - dish.current_price) /
                                                          dish.original_price) *
                                                          100
                                                  )
                                                : 0;
                                        const soldOut = dish.remaining_quantity <= 0;

                                        return (
                                            <div
                                                key={dish.id}
                                                className="flex flex-col justify-between gap-4 p-5 sm:flex-row sm:items-center"
                                            >
                                                <div className="space-y-1.5">
                                                    <div className="flex flex-wrap items-center gap-2">
                                                        <h4 className="text-base font-semibold text-gray-900">
                                                            {dish.name}
                                                        </h4>
                                                        {discountPct > 0 && (
                                                            <Badge variant="danger">-{discountPct}%</Badge>
                                                        )}
                                                        {dish.is_rule_discount_active && (
                                                            <Badge variant="warning">Giảm giờ vàng</Badge>
                                                        )}
                                                        <Badge variant={soldOut ? 'neutral' : 'success'}>
                                                            {soldOut
                                                                ? 'Hết suất'
                                                                : `Còn ${dish.remaining_quantity} suất`}
                                                        </Badge>
                                                    </div>

                                                    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                                                        <span className="inline-flex items-center gap-1">
                                                            <Clock className="h-3.5 w-3.5 text-emerald-600" />
                                                            Nhận món: {dish.pickup_window}
                                                        </span>
                                                        <span>Danh mục: {dish.category}</span>
                                                    </div>

                                                    {dish.allergens && dish.allergens.length > 0 && (
                                                        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                                                            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700">
                                                                <AlertTriangle className="h-3 w-3" />
                                                                Dị ứng:
                                                            </span>
                                                            {dish.allergens.map((al, idx) => (
                                                                <span
                                                                    key={`${dish.id}-al-${idx}`}
                                                                    className="rounded bg-amber-50 px-1.5 py-0.5 text-[11px] font-medium text-amber-800"
                                                                >
                                                                    {renderAllergenLabel(al)}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>

                                                <div className="flex items-center justify-between gap-4 sm:flex-col sm:items-end">
                                                    <div className="text-left sm:text-right">
                                                        <p className="text-lg font-bold text-emerald-700">
                                                            {formatVND(dish.current_price)}
                                                        </p>
                                                        {dish.original_price > dish.current_price && (
                                                            <p className="text-xs text-gray-400 line-through">
                                                                {formatVND(dish.original_price)}
                                                            </p>
                                                        )}
                                                    </div>

                                                    <Button
                                                        type="button"
                                                        size="sm"
                                                        disabled={soldOut}
                                                        onClick={() => openOrderModal(store, dish)}
                                                    >
                                                        <ShoppingBag className="h-4 w-4" />
                                                        {soldOut ? 'Đã hết' : 'Giải cứu ngay'}
                                                    </Button>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </Card>
                        );
                    })}
                </div>
            </div>

            {/* Rescue Order Modal */}
            <Modal
                isOpen={Boolean(activeDish)}
                onClose={closeOrderModal}
                title={createdOrder ? 'Đặt đơn giải cứu thành công' : 'Xác nhận giải cứu món ăn'}
            >
                {activeDish && !createdOrder && (
                    <div className="space-y-4">
                        <div className="rounded-xl border border-gray-100 bg-gray-50 p-3.5">
                            <p className="text-xs font-medium text-emerald-700">
                                {activeDish.store.name}
                            </p>
                            <p className="text-base font-bold text-gray-900">{activeDish.dish.name}</p>
                            <div className="mt-1 flex items-center justify-between text-xs text-gray-600">
                                <span>Đơn giá: {formatVND(activeDish.dish.current_price)}</span>
                                <span>Còn lại: {activeDish.dish.remaining_quantity} suất</span>
                            </div>
                        </div>

                        {!currentUser ? (
                            <div className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                                <p className="font-medium">
                                    Vui lòng đăng nhập tài khoản Người tiêu dùng (Consumer) để đặt đơn giải cứu.
                                </p>
                                <div className="flex gap-2">
                                    <Link
                                        href="/login"
                                        className="inline-flex items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                                    >
                                        Đi tới Đăng nhập
                                    </Link>
                                    <Button type="button" variant="ghost" onClick={closeOrderModal}>
                                        Đóng
                                    </Button>
                                </div>
                            </div>
                        ) : currentUser.role !== 'CONSUMER' ? (
                            <div className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                                <p>
                                    Bạn đang đăng nhập với vai trò <strong>{currentUser.role}</strong>. Chỉ tài khoản{' '}
                                    <strong>CONSUMER</strong> mới có thể đặt đơn giải cứu.
                                </p>
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => router.push('/login')}
                                >
                                    Đổi sang tài khoản Consumer
                                </Button>
                            </div>
                        ) : (
                            <form onSubmit={handleConfirmOrder} className="space-y-4">
                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-gray-700">
                                        Số lượng suất giải cứu
                                    </label>
                                    <div className="flex items-center gap-3">
                                        <button
                                            type="button"
                                            onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                                            className="h-9 w-9 rounded-lg border border-gray-300 text-base font-bold text-gray-700 hover:bg-gray-50"
                                        >
                                            -
                                        </button>
                                        <input
                                            type="number"
                                            min={1}
                                            max={Math.max(1, activeDish.dish.remaining_quantity)}
                                            value={quantity}
                                            onChange={(e) =>
                                                setQuantity(
                                                    Math.max(
                                                        1,
                                                        Math.min(
                                                            activeDish.dish.remaining_quantity,
                                                            Number(e.target.value) || 1
                                                        )
                                                    )
                                                )
                                            }
                                            className="h-9 w-20 rounded-lg border border-gray-300 text-center text-sm font-semibold"
                                        />
                                        <button
                                            type="button"
                                            onClick={() =>
                                                setQuantity((q) =>
                                                    Math.min(activeDish.dish.remaining_quantity, q + 1)
                                                )
                                            }
                                            className="h-9 w-9 rounded-lg border border-gray-300 text-base font-bold text-gray-700 hover:bg-gray-50"
                                        >
                                            +
                                        </button>
                                    </div>
                                </div>

                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-gray-700">
                                        Phương thức thanh toán
                                    </label>
                                    <div className="grid grid-cols-2 gap-2.5">
                                        {(['COD', 'VNPAY'] as PaymentMethod[]).map((method) => (
                                            <button
                                                key={method}
                                                type="button"
                                                onClick={() => setPaymentMethod(method)}
                                                className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                                                    paymentMethod === method
                                                        ? 'border-emerald-600 bg-emerald-50 text-emerald-700'
                                                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                                                }`}
                                            >
                                                {method === 'COD' ? 'Thanh toán tại quán (COD)' : 'Ví VNPAY'}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="space-y-1.5 rounded-xl bg-emerald-50/70 p-3.5 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Tổng thanh toán:</span>
                                        <span className="font-bold text-emerald-700">
                                            {formatVND(activeDish.dish.current_price * quantity)}
                                        </span>
                                    </div>
                                    <div className="flex justify-between text-xs text-gray-600">
                                        <span>Ước tính CO₂ tiết kiệm:</span>
                                        <span className="font-semibold text-emerald-700">
                                            ~{(quantity * 0.8).toFixed(1)} kg CO₂
                                        </span>
                                    </div>
                                    <div className="flex justify-between text-xs text-gray-600">
                                        <span>Green Points ước tính:</span>
                                        <span className="font-semibold text-emerald-700">
                                            +{quantity * 10} điểm
                                        </span>
                                    </div>
                                </div>

                                {orderError && (
                                    <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs font-medium text-red-700">
                                        {orderError}
                                    </div>
                                )}

                                <div className="flex justify-end gap-2 pt-2">
                                    <Button type="button" variant="ghost" onClick={closeOrderModal}>
                                        Hủy
                                    </Button>
                                    <Button
                                        type="submit"
                                        isLoading={createOrderMutation.isPending}
                                    >
                                        Xác nhận đặt đơn
                                    </Button>
                                </div>
                            </form>
                        )}
                    </div>
                )}

                {createdOrder && (
                    <div className="space-y-4">
                        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm">
                            <p className="font-bold text-emerald-900">
                                Mã đơn: {createdOrder.order_code}
                            </p>
                            <div className="mt-2 space-y-1 text-xs text-emerald-800">
                                <p>Tổng tiền: {formatVND(createdOrder.total_amount)}</p>
                                <p>
                                    CO₂ đã giải cứu: {Number(createdOrder.co2_saved_kg).toFixed(2)} kg
                                </p>
                                <p>Green Points: +{createdOrder.green_points_earned} điểm</p>
                            </div>
                        </div>

                        <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
                            <Button type="button" variant="outline" onClick={closeOrderModal}>
                                Tiếp tục khám phá
                            </Button>
                            <Button
                                type="button"
                                onClick={() => router.push(`/orders?highlight=${createdOrder.id}`)}
                            >
                                <QrCode className="h-4 w-4" />
                                Xem mã QR nhận món
                            </Button>
                        </div>
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
    );
}
