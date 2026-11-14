'use client';

import dynamic from 'next/dynamic';
import type { RadarMapProps } from './RadarMap';

export const DynamicRadarMap = dynamic<RadarMapProps>(
    () => import('./RadarMap').then((mod) => mod.default || mod),
    {
        ssr: false,
        loading: () => (
            <div className="flex h-[420px] w-full animate-pulse items-center justify-center rounded-2xl border border-gray-200 bg-gray-100 text-sm text-gray-500">
                Đang tải bản đồ Radar...
            </div>
        ),
    }
);
