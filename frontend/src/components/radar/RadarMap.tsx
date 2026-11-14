/* eslint-disable @next/next/no-img-element */
'use client';

import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { RescueDishItem } from '@/components/DishCard';

export interface RadarMapProps {
    center?: { lat: number; lng: number };
    radiusKm?: number;
    dishes?: RescueDishItem[];
    selectedDish?: RescueDishItem | null;
    onSelectDish?: (dish: RescueDishItem) => void;
    onRescueClick?: (dish: RescueDishItem) => void;
    onRecenter?: () => void;
}

export default function RadarMap({
    center = { lat: 10.7769, lng: 106.7009 },
    radiusKm = 3,
    dishes = [],
    selectedDish = null,
    onSelectDish,
    onRescueClick,
    onRecenter,
}: RadarMapProps) {
    const mapContainerRef = useRef<HTMLDivElement | null>(null);
    const mapInstanceRef = useRef<L.Map | null>(null);
    const layerGroupRef = useRef<L.LayerGroup | null>(null);

    useEffect(() => {
        if (!mapContainerRef.current || mapInstanceRef.current) return;

        const map = L.map(mapContainerRef.current, {
            center: [center.lat, center.lng],
            zoom: 14,
            zoomControl: false,
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors',
        }).addTo(map);

        layerGroupRef.current = L.layerGroup().addTo(map);
        mapInstanceRef.current = map;

        return () => {
            map.remove();
            mapInstanceRef.current = null;
        };
    }, [center.lat, center.lng]);

    useEffect(() => {
        const map = mapInstanceRef.current;
        const layerGroup = layerGroupRef.current;
        if (!map || !layerGroup) return;

        layerGroup.clearLayers();
        map.setView([center.lat, center.lng], radiusKm === 1 ? 15 : radiusKm === 3 ? 14 : 13);

        // Vòng tròn bán kính Radar
        L.circle([center.lat, center.lng], {
            radius: radiusKm * 1000,
            color: '#10B981',
            weight: 1.5,
            dashArray: '6, 6',
            fillColor: '#10B981',
            fillOpacity: 0.1,
        }).addTo(layerGroup);

        // Chấm xanh vị trí người dùng ("Bạn đang ở đây")
        const userIcon = L.divIcon({
            className: 'custom-user-marker',
            html: `<div style="display:flex;flex-direction:column;align-items:center;">
        <div style="width:16px;height:16px;border-radius:9999px;background:#2563EB;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>
        <span style="margin-top:4px;background:white;padding:2px 8px;border-radius:9999px;font-size:11px;font-weight:600;color:#1F2937;box-shadow:0 1px 4px rgba(0,0,0,0.15);white-space:nowrap;">Bạn đang ở đây</span>
      </div>`,
            iconSize: [100, 42],
            iconAnchor: [50, 10],
        });
        L.marker([center.lat, center.lng], { icon: userIcon }).addTo(layerGroup);

        // Các ghim giá tiền của quán ăn cứu trợ
        dishes.forEach((dish) => {
            const isSelected = selectedDish?.id === dish.id;
            const bg = isSelected ? '#0F8A5F' : '#FFFFFF';
            const color = isSelected ? '#FFFFFF' : '#0F8A5F';
            const priceText = dish.discountedPrice.toLocaleString('vi-VN') + 'đ';

            const storePin = L.divIcon({
                className: 'custom-store-marker',
                html: `<div style="display:inline-flex;align-items:center;gap:4px;background:${bg};color:${color};padding:5px 10px;border-radius:9999px;font-size:12px;font-weight:700;border:1.5px solid #0F8A5F;box-shadow:0 4px 10px rgba(0,0,0,0.15);white-space:nowrap;">
          <span>🛍</span><span>${priceText}</span>
        </div>`,
                iconSize: [96, 32],
                iconAnchor: [48, 16],
            });

            const marker = L.marker([dish.lat, dish.lng], { icon: storePin }).addTo(
                layerGroup
            );
            marker.on('click', () => onSelectDish?.(dish));
        });
    }, [center, radiusKm, dishes, selectedDish, onSelectDish]);

    const activeDish = selectedDish || dishes[0] || null;

    return (
        <div className="relative h-[520px] w-full overflow-hidden rounded-2xl border border-gray-200 bg-[#E8F0EB] lg:h-full">
            <link
                rel="stylesheet"
                href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
            />
            {/* Bản đồ nền Leaflet */}
            <div ref={mapContainerRef} className="z-0 h-full w-full" />

            {/* Hộp nổi góc trên bên trái: Radar đang quét */}
            <div className="absolute left-4 top-4 z-[400] flex items-center gap-3 rounded-2xl bg-white/95 px-4 py-2.5 shadow-md backdrop-blur">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#E6F7F0] text-sm text-[#10B981]">
                    ◎
                </span>
                <div>
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-gray-900">
                            Radar đang quét
                        </span>
                        <span className="h-2 w-2 rounded-full bg-[#10B981]" />
                    </div>
                    <p className="text-[11px] text-gray-500">
                        {dishes.length} điểm giải cứu gần bạn ({radiusKm} km)
                    </p>
                </div>
            </div>

            {/* Thẻ nổi chi tiết quán đang chọn (Góc dưới như Figma) */}
            {activeDish && (
                <div className="absolute bottom-14 right-16 z-[400] hidden w-72 items-center justify-between gap-3 rounded-2xl bg-white p-3 shadow-xl sm:flex">
                    <img
                        src={activeDish.imageUrl}
                        alt={activeDish.storeName}
                        className="h-14 w-14 rounded-xl object-cover"
                    />
                    <div className="flex-1 overflow-hidden">
                        <h4 className="truncate text-xs font-bold text-gray-900">
                            {activeDish.storeName}
                        </h4>
                        <p className="text-[11px] text-gray-500">
                            {activeDish.distanceText} • Nhận trước 18:30
                        </p>
                        <p className="mt-0.5 text-sm font-extrabold text-[#0F8A5F]">
                            {activeDish.discountedPrice.toLocaleString('vi-VN')}đ
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={() => onRescueClick?.(activeDish)}
                        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#E6F7F0] text-xs font-bold text-[#0F8A5F] hover:bg-[#10B981] hover:text-white"
                    >
                        →
                    </button>
                </div>
            )}

            {/* Chú thích góc dưới bên trái */}
            <div className="absolute bottom-4 left-4 z-[400] flex items-center gap-3 rounded-full bg-white/95 px-3.5 py-1.5 text-[11px] font-medium text-gray-600 shadow-sm">
                <span className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-[#10B981]" /> Điểm giải cứu
                </span>
                <span className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-[#2563EB]" /> Vị trí của bạn
                </span>
            </div>

            {/* Cụm nút điều khiển Zoom & Định vị góc dưới bên phải */}
            <div className="absolute bottom-4 right-4 z-[400] flex flex-col overflow-hidden rounded-xl bg-white shadow-md">
                <button
                    type="button"
                    onClick={() => mapInstanceRef.current?.zoomIn()}
                    className="border-b border-gray-100 px-3 py-2 text-sm font-bold text-gray-700 hover:bg-gray-50"
                >
                    +
                </button>
                <button
                    type="button"
                    onClick={() => mapInstanceRef.current?.zoomOut()}
                    className="border-b border-gray-100 px-3 py-2 text-sm font-bold text-gray-700 hover:bg-gray-50"
                >
                    −
                </button>
                <button
                    type="button"
                    onClick={onRecenter}
                    title="Định vị lại GPS"
                    className="px-3 py-2 text-xs text-gray-700 hover:bg-gray-50"
                >
                    🎯
                </button>
            </div>
        </div>
    );
}