import type { Metadata } from 'next';
import React from 'react';
import './globals.css';
import QueryProvider from '@/providers/QueryProvider';
import { Navbar } from '@/components/ui/Navbar';
import { BottomNavigation } from '@/components/ui/BottomNavigation';

export const metadata: Metadata = {
    title: 'EcoBite — Giải cứu Thực phẩm Dư thừa Thông minh',
    description:
        'Nền tảng kết nối đồ ăn dư chất lượng với giá ưu đãi theo khung giờ, bảo vệ môi trường và tích Điểm Xanh.',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="vi">
            <body className="min-h-screen bg-gray-50 pb-20 md:pb-8">
                <QueryProvider>
                    <Navbar />
                    <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                        {children}
                    </main>
                    <BottomNavigation />
                </QueryProvider>
            </body>
        </html>
    );
}
