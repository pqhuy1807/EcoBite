'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { DishCard, RescueDishItem } from '@/components/DishCard';
import { OrderModal } from '@/components/OrderModal';
import { DynamicRadarMap } from '@/components/radar/DynamicRadarMap';
import { useGeolocation } from '@/hooks/useGeolocation';
import { discoveryService } from '@/services/discovery.service';
import type { NearbyStore } from '@/types/api';

const DEFAULT_DISH_IMAGE =
    'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80';

const FALLBACK_DEMO_DISHES: RescueDishItem[] = [
    {
        id: 'dish-1',
        name: 'Combo Bánh Mì & Cà Phê Sữa',
        storeName: 'Bánh Mì Ơi',
        storeAddress: 'Nguyễn Thị Minh Khai',
        distanceText: '450m',
        originalPrice: 50000,
        discountedPrice: 25000,
        discountPercent: 50,
        remainingQuantity: 3,
        tagCaption: 'Bữa sáng trọn vị',
        countdownSeconds: 4530,
        imageUrl:
            'https://images.unsplash.com/photo-1509722747041-616f39b57569?auto=format&fit=crop&w=400&q=80',
        category: 'BAKERY',
        lat: 10.7805,
        lng: 106.6985,
    },
    {
        id: 'dish-2',
        name: 'Cơm Tấm Sườn Bì Chả',
        storeName: 'Cơm Tấm Chú Ba',
        storeAddress: 'Nguyễn Trãi',
        distanceText: '800m',
        originalPrice: 60000,
        discountedPrice: 30000,
        discountPercent: 50,
        remainingQuantity: 3,
        tagCaption: 'Bữa trưa đủ đầy',
        countdownSeconds: 2712,
        imageUrl:
            'https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=400&q=80',
        category: 'RICE',
        lat: 10.7725,
        lng: 106.6945,
    },
    {
        id: 'dish-3',
        name: 'Hộp Bánh Ngọt Mix Cuối Ngày',
        storeName: 'Lumière Bakery',
        storeAddress: 'Lê Thánh Tôn',
        distanceText: '1,2 km',
        originalPrice: 120000,
        discountedPrice: 36000,
        discountPercent: 70,
        remainingQuantity: 3,
        tagCaption: 'Ngọt ngào bất ngờ',
        countdownSeconds: 7805,
        imageUrl:
            'https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=400&q=80',
        category: 'BAKERY',
        lat: 10.7792,
        lng: 106.7052,
    },
];

type CategoryFilter = 'ALL' | 'RICE' | 'NOODLES' | 'BAKERY' | 'VEGETARIAN';

function formatDistanceMeters(meters: number): string {
    if (!Number.isFinite(meters) || meters < 0) return 'Gần bạn';
    if (meters < 1000) return `${Math.round(meters)}m`;
    return `${(meters / 1000).toFixed(1).replace('.', ',')} km`;
}

function estimateCountdownSeconds(pickupWindow: string): number {
    const matches = pickupWindow.match(/(\d{1,2}):(\d{2})/g);
    if (!matches || matches.length === 0) return 3600;
    const endPart = matches[matches.length - 1];
    const [hours, minutes] = endPart.split(':').map(Number);
    if (Number.isNaN(hours) || Number.isNaN(minutes)) return 3600;

    const now = new Date();
    const target = new Date(now);
    target.setHours(hours, minutes, 0, 0);
    const diff = Math.floor((target.getTime() - now.getTime()) / 1000);
    return diff > 0 ? diff : 1800;
}

function mapNearbyStoresToDishes(stores: NearbyStore[]): RescueDishItem[] {
    const mapped: RescueDishItem[] = [];

    for (const store of stores) {
        const distanceText = formatDistanceMeters(store.distance_meters);
        for (const dish of store.dishes) {
            const originalPrice = Number(dish.original_price) || 0;
            const discountedPrice = Number(dish.current_price) || originalPrice;
            const discountPercent =
                originalPrice > 0
                    ? Math.max(
                        0,
                        Math.round(((originalPrice - discountedPrice) / originalPrice) * 100)
                    )
                    : 0;

            mapped.push({
                id: dish.id,
                name: dish.name,
                storeName: store.name,
                storeAddress: store.address,
                distanceText,
                originalPrice,
                discountedPrice,
                discountPercent,
                remainingQuantity: dish.remaining_quantity,
                tagCaption: dish.is_rule_discount_active
                    ? `Giảm giờ chót • Nhận ${dish.pickup_window}`
                    : `Nhận món: ${dish.pickup_window}`,
                countdownSeconds: estimateCountdownSeconds(dish.pickup_window),
                imageUrl: dish.image_url || DEFAULT_DISH_IMAGE,
                category: dish.category as RescueDishItem['category'],
                lat: store.latitude,
                lng: store.longitude,
            });
        }
    }

    return mapped;
}

export default function HomeRadarPage() {
    const { coords, refreshLocation } = useGeolocation();
    const [radiusKm, setRadiusKm] = useState<number>(5);
    const [category, setCategory] = useState<CategoryFilter>('ALL');
    const [searchQuery, setSearchQuery] = useState('');
    const [dishes, setDishes] = useState<RescueDishItem[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [usingDemoData, setUsingDemoData] = useState<boolean>(false);
    const [selectedDish, setSelectedDish] = useState<RescueDishItem | null>(null);
    const [modalDish, setModalDish] = useState<RescueDishItem | null>(null);

    const fetchNearbyDishes = useCallback(async () => {
        setLoading(true);
        try {
            const res = await discoveryService.getNearbyStores({
                lat: coords.lat,
                lng: coords.lng,
                radius_km: radiusKm,
            });
            const liveDishes = mapNearbyStoresToDishes(res.results ?? []);
            setDishes(liveDishes);
            setSelectedDish((prev) =>
                prev && liveDishes.some((item) => item.id === prev.id)
                    ? prev
                    : (liveDishes[0] ?? null)
            );
            setUsingDemoData(false);
        } catch {
            setDishes(FALLBACK_DEMO_DISHES);
            setSelectedDish((prev) => prev ?? FALLBACK_DEMO_DISHES[0]);
            setUsingDemoData(true);
        } finally {
            setLoading(false);
        }
    }, [coords.lat, coords.lng, radiusKm]);

    useEffect(() => {
        void fetchNearbyDishes();
    }, [fetchNearbyDishes]);

    const filteredDishes = useMemo(() => {
        const keyword = searchQuery.trim().toLowerCase();
        return dishes.filter((item) => {
            const matchCategory = category === 'ALL' || item.category === category;
            const matchQuery =
                !keyword ||
                item.name.toLowerCase().includes(keyword) ||
                item.storeName.toLowerCase().includes(keyword) ||
                item.storeAddress.toLowerCase().includes(keyword);
            return matchCategory && matchQuery;
        });
    }, [dishes, category, searchQuery]);

    const handleOrderSuccess = (dishId: string, quantityBought: number) => {
        setDishes((prev) =>
            prev.map((d) =>
                d.id === dishId
                    ? {
                        ...d,
                        remainingQuantity: Math.max(
                            0,
                            d.remainingQuantity - quantityBought
                        ),
                    }
                    : d
            )
        );
    };

    return (
        <div className="space-y-5">
            {/* Thanh công cụ tìm kiếm, vị trí, bán kính và danh mục */}
            <section className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div className="flex flex-wrap items-center gap-2.5">
                        <button
                            type="button"
                            onClick={refreshLocation}
                            className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-100"
                        >
                            <span>📍</span>
                            <span>
                                {coords.lat.toFixed(4)}, {coords.lng.toFixed(4)}
                            </span>
                            <span className="text-emerald-600">↻</span>
                        </button>

                        <div className="flex items-center gap-1.5">
                            <span className="text-xs font-medium text-gray-500">
                                Bán kính:
                            </span>
                            {[1, 3, 5, 10].map((km) => (
                                <button
                                    key={km}
                                    type="button"
                                    onClick={() => setRadiusKm(km)}
                                    className={`rounded-full px-3 py-1 text-xs font-semibold transition ${radiusKm === km
                                            ? 'bg-emerald-600 text-white shadow-sm'
                                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }`}
                                >
                                    {km} km
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="w-full md:max-w-sm">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Tìm kiếm món ăn, tên quán, địa chỉ..."
                            className="w-full rounded-full border border-gray-200 bg-gray-50 px-4 py-2 text-xs text-gray-800 outline-none focus:border-emerald-500 focus:bg-white"
                        />
                    </div>
                </div>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 pt-3">
                    <div className="flex flex-wrap items-center gap-1.5">
                        {[
                            { id: 'ALL', label: 'Tất cả' },
                            { id: 'RICE', label: 'Cơm' },
                            { id: 'NOODLES', label: 'Mì & Bún' },
                            { id: 'BAKERY', label: 'Bánh ngọt' },
                            { id: 'VEGETARIAN', label: 'Đồ chay' },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                type="button"
                                onClick={() => setCategory(tab.id as CategoryFilter)}
                                className={`rounded-full border px-3 py-1 text-xs font-medium transition ${category === tab.id
                                        ? 'border-emerald-600 bg-emerald-50 font-semibold text-emerald-800'
                                        : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                                    }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    <button
                        type="button"
                        onClick={() => void fetchNearbyDishes()}
                        disabled={loading}
                        className="text-xs font-semibold text-emerald-700 hover:underline disabled:opacity-50"
                    >
                        {loading ? 'Đang quét Radar...' : 'Làm mới Radar'}
                    </button>
                </div>

                {usingDemoData && (
                    <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-2 text-xs text-amber-800">
                        Không kết nối được API máy chủ cục bộ — đang hiển thị dữ liệu mẫu minh họa.
                    </div>
                )}
            </section>

            {/* Bố cục Split-Screen: Danh sách Món - Bản đồ Radar */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
                <div className="flex flex-col justify-between lg:col-span-5">
                    <div>
                        <div className="mb-4 flex items-end justify-between">
                            <div>
                                <p className="text-[11px] font-extrabold uppercase tracking-wider text-emerald-700">
                                    ĂN NGON. SỐNG XANH.
                                </p>
                                <h1 className="text-2xl font-extrabold text-gray-900">
                                    Món ngon đang chờ bạn
                                </h1>
                                <p className="text-xs text-gray-500">
                                    {filteredDishes.length} suất giải cứu trong bán kính {radiusKm}{' '}
                                    km
                                </p>
                            </div>
                        </div>

                        {loading ? (
                            <div className="space-y-3.5">
                                {[1, 2, 3].map((skeleton) => (
                                    <div
                                        key={skeleton}
                                        className="h-32 animate-pulse rounded-2xl border border-gray-200 bg-gray-100"
                                    />
                                ))}
                            </div>
                        ) : filteredDishes.length === 0 ? (
                            <div className="rounded-2xl border border-gray-100 bg-white p-8 text-center shadow-sm">
                                <p className="text-sm font-bold text-gray-800">
                                    Không tìm thấy món ăn nào trong bán kính {radiusKm} km
                                </p>
                                <p className="mt-1 text-xs text-gray-500">
                                    Hãy thử mở rộng phạm vi tìm kiếm hoặc chọn danh mục khác.
                                </p>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setRadiusKm(10);
                                        setCategory('ALL');
                                        setSearchQuery('');
                                    }}
                                    className="mt-4 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-700"
                                >
                                    Mở rộng bán kính lên 10 km
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-3.5">
                                {filteredDishes.map((dish) => (
                                    <DishCard
                                        key={dish.id}
                                        dish={dish}
                                        isSelected={selectedDish?.id === dish.id}
                                        onSelectDish={(d) => setSelectedDish(d)}
                                        onRescueClick={(d) => setModalDish(d)}
                                    />
                                ))}
                            </div>
                        )}
                    </div>

                    <p className="mt-6 text-center text-xs text-gray-400">
                        Mỗi món được cứu, một chút xanh cho thành phố.
                    </p>
                </div>

                <div className="lg:col-span-7">
                    <DynamicRadarMap
                        center={coords}
                        radiusKm={radiusKm}
                        dishes={filteredDishes}
                        selectedDish={selectedDish}
                        onSelectDish={(d) => setSelectedDish(d)}
                        onRescueClick={(d) => setModalDish(d)}
                        onRecenter={refreshLocation}
                    />
                </div>
            </div>

            {modalDish && (
                <OrderModal
                    dish={modalDish}
                    onClose={() => setModalDish(null)}
                    onOrderSuccess={handleOrderSuccess}
                />
            )}
        </div>
    );
}