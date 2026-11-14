'use client';

import React, { useEffect, useMemo } from 'react';
import L from 'leaflet';
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import type { NearbyStore } from '@/types/api';
import { formatDistance, formatVND } from '@/lib/utils';

export interface RadarMapProps {
    userLocation: { lat: number; lng: number };
    radiusKm: number;
    stores: NearbyStore[];
    selectedStoreId: string | null;
    onSelectStore?: (storeId: string) => void;
}

function MapViewportController({
    center,
    radiusKm,
}: {
    center: [number, number];
    radiusKm: number;
}) {
    const map = useMap();

    useEffect(() => {
        const zoom = radiusKm <= 2 ? 14 : radiusKm <= 5 ? 13 : 12;
        map.setView(center, zoom, { animate: true });
    }, [center, radiusKm, map]);

    return null;
}

function createUserIcon(): L.DivIcon {
    return L.divIcon({
        className: 'ecobite-user-pin',
        html: `<div style="position:relative;width:20px;height:20px;display:flex;align-items:center;justify-content:center;">
            <span style="position:absolute;width:24px;height:24px;border-radius:9999px;background:rgba(37,99,235,0.28);"></span>
            <span style="width:12px;height:12px;border-radius:9999px;background:#2563eb;border:2px solid #ffffff;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></span>
        </div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
    });
}

function createStoreIcon(dishCount: number, isSelected: boolean): L.DivIcon {
    const bg = isSelected ? '#047857' : '#10b981';
    const border = isSelected ? '3px solid #fde047' : '2px solid #ffffff';
    const scale = isSelected ? 'transform:scale(1.12);' : '';
    return L.divIcon({
        className: 'ecobite-store-pin',
        html: `<div style="display:inline-flex;align-items:center;justify-content:center;min-width:34px;height:34px;padding:0 8px;border-radius:9999px;background:${bg};color:#ffffff;font-weight:700;font-size:12px;border:${border};box-shadow:0 4px 10px rgba(0,0,0,0.25);${scale}">
            ${dishCount} món
        </div>`,
        iconSize: [52, 34],
        iconAnchor: [26, 17],
    });
}

export default function RadarMap({
    userLocation,
    radiusKm,
    stores,
    selectedStoreId,
    onSelectStore,
}: RadarMapProps) {
    const userCenter = useMemo<[number, number]>(
        () => [userLocation.lat, userLocation.lng],
        [userLocation.lat, userLocation.lng]
    );
    const userIcon = useMemo(() => createUserIcon(), []);

    return (
        <div className="relative h-[420px] w-full overflow-hidden rounded-2xl border border-gray-200 shadow-sm">
            <MapContainer
                center={userCenter}
                zoom={13}
                scrollWheelZoom
                className="h-full w-full z-10"
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <MapViewportController center={userCenter} radiusKm={radiusKm} />

                <Circle
                    center={userCenter}
                    radius={radiusKm * 1000}
                    pathOptions={{
                        color: '#059669',
                        fillColor: '#10b981',
                        fillOpacity: 0.1,
                        weight: 2,
                        dashArray: '6 6',
                    }}
                />

                <Marker position={userCenter} icon={userIcon}>
                    <Popup>
                        <div className="text-xs font-medium text-gray-800">
                            Vị trí của bạn ({userLocation.lat.toFixed(4)}, {userLocation.lng.toFixed(4)})
                        </div>
                    </Popup>
                </Marker>

                {stores.map((store) => {
                    const isSelected = selectedStoreId === store.id;
                    const firstDish = store.dishes[0];
                    return (
                        <Marker
                            key={store.id}
                            position={[store.latitude, store.longitude]}
                            icon={createStoreIcon(store.dishes.length, isSelected)}
                            eventHandlers={{
                                click: () => onSelectStore?.(store.id),
                            }}
                        >
                            <Popup>
                                <div className="min-w-[200px] space-y-1.5 text-xs">
                                    <p className="text-sm font-bold text-gray-900">{store.name}</p>
                                    <p className="text-gray-600">{store.address}</p>
                                    <div className="flex items-center justify-between pt-1 text-[11px] font-medium text-emerald-700">
                                        <span>Cách {formatDistance(store.distance_meters)}</span>
                                        <span>★ {Number(store.rating_avg || 5).toFixed(1)}</span>
                                    </div>
                                    {firstDish && (
                                        <div className="rounded-md bg-emerald-50 p-1.5 text-[11px] text-emerald-900">
                                            <p className="font-semibold">{firstDish.name}</p>
                                            <p>
                                                {formatVND(firstDish.current_price)} • Còn{' '}
                                                {firstDish.remaining_quantity} suất
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>
        </div>
    );
}
