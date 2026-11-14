'use client';

import React, { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { DishCard, RescueDishItem } from '@/components/DishCard';
import { OrderModal } from '@/components/OrderModal';
import { DynamicRadarMap } from '@/components/radar/DynamicRadarMap';
import { useGeolocation } from '@/hooks/useGeolocation';
import { discoveryService } from '@/services/discovery.service';

const INITIAL_DISHES: RescueDishItem[] = [
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
        countdownSeconds: 4530, // 01:15:30
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
        countdownSeconds: 2712, // 00:45:12
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
        countdownSeconds: 7805, // 02:10:05
        imageUrl:
            'https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=400&q=80',
        category: 'BAKERY',
        lat: 10.7792,
        lng: 106.7052,
    },
];

type CategoryFilter = 'ALL' | 'RICE' | 'NOODLES' | 'BAKERY' | 'VEGETARIAN';

export default function HomeRadarPage() {
    const { coords, refreshLocation } = useGeolocation();
    const [radiusKm, setRadiusKm] = useState<number>(3);
    const [category, setCategory] = useState<CategoryFilter>('ALL');
    const [searchQuery, setSearchQuery] = useState('');
    const [dishes, setDishes] = useState<RescueDishItem[]>(INITIAL_DISHES);
    const [selectedDish, setSelectedDish] = useState<RescueDishItem | null>(
        INITIAL_DISHES[0]
    );
    const [modalDish, setModalDish] = useState<RescueDishItem | null>(null);
    const [myOrdersCount, setMyOrdersCount] = useState<number>(2);

    // Gọi API PostGIS Radar khi tọa độ hoặc bán kính thay đổi
    useEffect(() => {
        discoveryService
            .getNearbyStores({
                lat: coords.lat,
                lng: coords.lng,
                radius_km: radiusKm,
            })
            .catch(() => {
                // Giữ danh sách mẫu nếu Backend local chưa bật
            });
    }, [coords.lat, coords.lng, radiusKm]);

    const filteredDishes = useMemo(() => {
        return dishes.filter((item) => {
            const matchCategory = category === 'ALL' || item.category === category;
            const matchQuery =
                !searchQuery ||
                item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                item.storeName.toLowerCase().includes(searchQuery.toLowerCase());
            return matchCategory && matchQuery;
        });
    }, [dishes, category, searchQuery]);

    const handleOrderSuccess = (dishId: string, quantityBought: number) => {
        setMyOrdersCount((c) => c + 1);
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
        <div className="flex min-h-screen flex-col bg-[#F8FAFC]">
            {/* 1. Thanh Điều hướng Trên cùng (Navbar từ Figma image_49ba2d.jpg) */}
            <header className="sticky top-0 z-30 border-b border-gray-100 bg-white px-4 py-3 sm:px-6">
                <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                        <Link href="/" className="flex items-center gap-2">
                            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#10B981] text-sm text-white">
                                🍃
                            </span>
                            <span className="text-lg font-extrabold tracking-tight text-gray-900">
                                EcoBite
                            </span>
                        </Link>

                        <button
                            type="button"
                            onClick={refreshLocation}
                            className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200"
                        >
                            <span className="text-[#10B981]">📍</span>
                            <span>Quận 1, TP.HCM</span>
                            <span className="text-gray-400">↻</span>
                        </button>
                    </div>

                    {/* Ô tìm kiếm */}
                    <div className="order-3 w-full md:order-2 md:max-w-md">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="🔍 Tìm kiếm món ăn, tên quán..."
                            className="w-full rounded-full border border-gray-200 bg-gray-50 px-4 py-2 text-xs text-gray-800 outline-none focus:border-[#10B981] focus:bg-white"
                        />
                    </div>

                    {/* Đơn giải cứu & Tài khoản */}
                    <div className="order-2 flex items-center gap-3 md:order-3">
                        <Link
                            href="/orders"
                            className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                        >
                            <span>🛍 Đơn giải cứu của tôi</span>
                            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#F97316] text-[10px] font-bold text-white">
                                {myOrdersCount}
                            </span>
                        </Link>
                        <Link
                            href="/login"
                            className="flex h-8 w-8 items-center justify-center rounded-full bg-[#E6F7F0] text-xs font-bold text-[#0F8A5F]"
                            title="Đăng nhập / Tài khoản"
                        >
                            T
                        </Link>
                    </div>
                </div>
            </header>

            {/* 2. Thanh Công cụ Lọc Bán kính & Danh mục Món (Từ Figma image_49ba2d.jpg) */}
            <div className="border-b border-gray-100 bg-white px-4 py-2.5 sm:px-6">
                <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3">
                    {/* Chọn bán kính quét */}
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-gray-500">
                            Bán kính quét:
                        </span>
                        {[1, 3, 5].map((km) => (
                            <button
                                key={km}
                                type="button"
                                onClick={() => setRadiusKm(km)}
                                className={`rounded-full px-3 py-1 text-xs font-semibold transition ${radiusKm === km
                                    ? 'bg-[#10B981] text-white shadow-sm'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                    }`}
                            >
                                {km} km
                            </button>
                        ))}
                    </div>

                    {/* Lọc danh mục món ăn */}
                    <div className="flex flex-wrap items-center gap-1.5">
                        <span className="mr-1 hidden text-xs text-gray-400 sm:inline">
                            Khám phá theo món
                        </span>
                        {[
                            { id: 'ALL', label: 'Tất cả' },
                            { id: 'RICE', label: '🍚 Cơm' },
                            { id: 'NOODLES', label: '🍜 Mì & Bún' },
                            { id: 'BAKERY', label: '🥐 Bánh ngọt' },
                            { id: 'VEGETARIAN', label: '🥗 Đồ chay' },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                type="button"
                                onClick={() => setCategory(tab.id as CategoryFilter)}
                                className={`rounded-full border px-3 py-1 text-xs font-medium transition ${category === tab.id
                                    ? 'border-[#10B981] bg-[#E6F7F0] font-semibold text-[#0F8A5F]'
                                    : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                                    }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* 3. Bố cục Split-Screen: Cột trái Danh sách Món - Cột phải Bản đồ Radar */}
            <main className="mx-auto grid w-full max-w-7xl flex-1 grid-cols-1 gap-6 p-4 sm:p-6 lg:grid-cols-12">
                {/* Cột trái (5/12): Danh sách thẻ món ăn giải cứu */}
                <div className="flex flex-col justify-between lg:col-span-5">
                    <div>
                        <div className="mb-4 flex items-end justify-between">
                            <div>
                                <p className="text-[11px] font-extrabold uppercase tracking-wider text-[#0F8A5F]">
                                    ĂN NGON. SỐNG XANH.
                                </p>
                                <h1 className="text-2xl font-extrabold text-gray-900">
                                    Món ngon đang chờ bạn
                                </h1>
                                <p className="text-xs text-gray-500">
                                    {filteredDishes.length} túi bất ngờ trong bán kính {radiusKm}{' '}
                                    km
                                </p>
                            </div>

                            <span className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700">
                                Gần bạn nhất ⌄
                            </span>
                        </div>

                        {filteredDishes.length === 0 ? (
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
                                        setRadiusKm(5);
                                        setCategory('ALL');
                                    }}
                                    className="mt-4 rounded-xl bg-[#10B981] px-4 py-2 text-xs font-semibold text-white"
                                >
                                    Mở rộng bán kính lên 5 km
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
                        🍃 Mỗi món được cứu, một chút xanh cho thành phố.
                    </p>
                </div>

                {/* Cột phải (7/12): Bản đồ Radar Tương tác */}
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
            </main>

            {/* Modal Đặt hàng & Xác nhận Đơn */}
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