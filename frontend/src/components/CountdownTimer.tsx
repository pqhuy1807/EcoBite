'use client';

import React, { useEffect, useState } from 'react';

interface CountdownTimerProps {
    targetTime?: string;
    initialSeconds?: number;
}

export function CountdownTimer({
    targetTime,
    initialSeconds = 4530, // Mặc định 01:15:30 như Figma
}: CountdownTimerProps) {
    const [secondsLeft, setSecondsLeft] = useState<number>(() => {
        if (targetTime) {
            const diff = Math.floor(
                (new Date(targetTime).getTime() - Date.now()) / 1000
            );
            return diff > 0 ? diff : initialSeconds;
        }
        return initialSeconds;
    });

    useEffect(() => {
        const timer = setInterval(() => {
            setSecondsLeft((prev) => (prev > 0 ? prev - 1 : 0));
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    const hours = String(Math.floor(secondsLeft / 3600)).padStart(2, '0');
    const minutes = String(Math.floor((secondsLeft % 3600) / 60)).padStart(
        2,
        '0'
    );
    const seconds = String(secondsLeft % 60).padStart(2, '0');

    return (
        <div className="inline-flex items-center gap-1.5 text-xs font-medium text-[#B45309]">
            <span>⏱</span>
            <span>
                Còn {hours}:{minutes}:{seconds} để đón món
            </span>
        </div>
    );
}

export default CountdownTimer;