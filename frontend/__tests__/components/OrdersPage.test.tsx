import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import MyOrdersPage from '@/app/orders/page';
import { orderService } from '@/services/order.service';
import { paymentService } from '@/services/payment.service';
import type { OrderResponse } from '@/types/api';

vi.mock('@/components/auth/AuthGuard', () => ({
    AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('next/link', () => ({
    default: ({
        href,
        children,
        className,
    }: {
        href: string;
        children: React.ReactNode;
        className?: string;
    }) => (
        <a href={href} className={className}>
            {children}
        </a>
    ),
}));

vi.mock('@/services/order.service', () => ({
    orderService: {
        getMyOrders: vi.fn(),
        issueOrderQr: vi.fn(),
        cancelOrder: vi.fn(),
    },
}));

vi.mock('@/services/payment.service', () => ({
    paymentService: {
        createVnpayUrl: vi.fn(),
    },
}));

vi.mock('@/services/review.service', () => ({
    reviewService: {
        createOrderReview: vi.fn(),
    },
}));

function makeOrder(overrides: Partial<OrderResponse>): OrderResponse {
    return {
        id: 'order-1',
        order_code: 'EB-20261128-0001',
        consumer_id: 'user-1',
        store_id: 'store-1',
        dish_id: 'dish-1',
        dish_name: 'Cơm Tấm Sườn Bì Chả',
        store_name: 'Cơm Tấm Chú Ba',
        store_address: '123 Nguyễn Trãi',
        quantity: 1,
        unit_price: 25000,
        total_amount: 25000,
        status: 'CONFIRMED',
        payment_method: 'VNPAY',
        payment_status: 'PENDING',
        co2_saved_kg: 2.5,
        green_points_earned: 25,
        pickup_deadline: '2026-11-28T20:00:00Z',
        created_at: '2026-11-28T15:00:00Z',
        ...overrides,
    } as OrderResponse;
}

function renderWithQueryClient(ui: React.ReactElement) {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
        },
    });
    return render(
        <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    );
}

describe('MyOrdersPage — VNPay Retry & QR Guard', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('khóa nút Xem mã QR và hiển thị nút Thanh toán VNPay ngay với đơn VNPAY đang PENDING', async () => {
        vi.mocked(orderService.getMyOrders).mockResolvedValue([
            makeOrder({
                id: 'ord-pending-vnpay',
                order_code: 'EB-20261128-VNP1',
                payment_method: 'VNPAY',
                payment_status: 'PENDING',
                status: 'CONFIRMED',
            }),
        ]);
        vi.mocked(paymentService.createVnpayUrl).mockResolvedValue({
            payment_url: 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?vnp_TxnRef=1',
            txn_ref: 'EB-20261128-VNP1',
        });

        renderWithQueryClient(<MyOrdersPage />);

        expect(await screen.findByText('Chờ thanh toán VNPay')).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Xem mã QR/i })).not.toBeInTheDocument();

        const payButton = screen.getByRole('button', { name: /Thanh toán VNPay ngay/i });
        fireEvent.click(payButton);

        await waitFor(() => {
            expect(paymentService.createVnpayUrl).toHaveBeenCalledWith('ord-pending-vnpay');
        });
    });

    it('mở nút Xem mã QR và ẩn nút thanh toán VNPay khi đơn VNPAY đã PAID', async () => {
        vi.mocked(orderService.getMyOrders).mockResolvedValue([
            makeOrder({
                id: 'ord-paid-vnpay',
                order_code: 'EB-20261128-VNP2',
                payment_method: 'VNPAY',
                payment_status: 'PAID',
                status: 'CONFIRMED',
            }),
        ]);

        renderWithQueryClient(<MyOrdersPage />);

        expect(await screen.findByRole('button', { name: /Xem mã QR/i })).toBeInTheDocument();
        expect(screen.queryByText('Chờ thanh toán VNPay')).not.toBeInTheDocument();
        expect(
            screen.queryByRole('button', { name: /Thanh toán VNPay ngay/i })
        ).not.toBeInTheDocument();
    });

    it('cho phép mở nút Xem mã QR bình thường với đơn COD đang PENDING', async () => {
        vi.mocked(orderService.getMyOrders).mockResolvedValue([
            makeOrder({
                id: 'ord-cod',
                order_code: 'EB-20261128-COD1',
                payment_method: 'COD',
                payment_status: 'PENDING',
                status: 'CONFIRMED',
            }),
        ]);

        renderWithQueryClient(<MyOrdersPage />);

        expect(await screen.findByRole('button', { name: /Xem mã QR/i })).toBeInTheDocument();
        expect(
            screen.queryByRole('button', { name: /Thanh toán VNPay ngay/i })
        ).not.toBeInTheDocument();
    });
});