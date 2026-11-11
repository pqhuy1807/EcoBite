'use client';

import { useState, useEffect, useCallback } from 'react';

export interface Coordinates {
    lat: number;
    lng: number;
}

interface GeolocationState {
    coords: Coordinates;
    isLoading: boolean;
    error: string | null;
    isFallback: boolean;
}

// Tọa độ mặc định: Trung tâm Quận 1, TP.HCM
const DEFAULT_HCMC_COORDS: Coordinates = {
    lat: 10.7769,
    lng: 106.7009,
};

export function useGeolocation() {
    const [state, setState] = useState<GeolocationState>({
        coords: DEFAULT_HCMC_COORDS,
        isLoading: true,
        error: null,
        isFallback: false,
    });

    const requestLocation = useCallback(() => {
        if (typeof window === 'undefined' || !('geolocation' in navigator)) {
            setState({
                coords: DEFAULT_HCMC_COORDS,
                isLoading: false,
                error: 'Trình duyệt không hỗ trợ định vị GPS.',
                isFallback: true,
            });
            return;
        }

        setState((prev) => ({ ...prev, isLoading: true, error: null }));

        navigator.geolocation.getCurrentPosition(
            (position) => {
                setState({
                    coords: {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                    },
                    isLoading: false,
                    error: null,
                    isFallback: false,
                });
            },
            (err) => {
                setState({
                    coords: DEFAULT_HCMC_COORDS,
                    isLoading: false,
                    error: err.message || 'Không thể lấy vị trí hiện tại, đang dùng vị trí mặc định.',
                    isFallback: true,
                });
            },
            {
                enableHighAccuracy: true,
                timeout: 8000,
                maximumAge: 60000,
            }
        );
    }, []);

    useEffect(() => {
        requestLocation();
    }, [requestLocation]);

    return {
        ...state,
        refreshLocation: requestLocation,
    };
}