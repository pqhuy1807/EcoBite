'use client';

import dynamic from 'next/dynamic';

export const DynamicRadarMap = dynamic(
    () => import('./RadarMap').then((mod) => mod.default || mod),
    {
        ssr: false,
        loading: () => (
            <div className="flex h-[450px] w-full animate-pulse items-center justify-center rounded-xl bg-gray-100 text-sm text-gray-500">
                Đang tải bản đồ Radar...
            </div>
        ),
    }
);