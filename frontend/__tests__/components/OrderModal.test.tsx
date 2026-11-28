import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { OrderModal } from '@/components/OrderModal';
import type { RescueDishItem } from '@/components/DishCard';
import { orderService } from '@/services/order.service';
import { paymentService } from '@/services/payment.service';

vi.mock('@/services/order.service', () => ({
    orderService: {
        createRescueOrder: vi.fn(),
    },
}));

vi.mock('@/services/payment.service', () => ({
    paymentService: {
        createVnpayUrl: vi.fn(),
    },
}));

const MOCK_DISH: RescueDishItem = {
    id: 'dish-101',
    name: 'Cơm Tấm Sườn Bì Chả',
    storeName: 'Cơm Tấm Chú Ba',
    storeAddress: 'Nguyễn Trãi, Q1',
    distanceText: '800m',
    originalPrice: 60000,
    discountedPrice: 30000,
    discountPercent: 50,
    remainingQuantity: 3,
    tagCaption: 'Bữa trưa đủ đầy',
    countdownSeconds: 3600,
    imageUrl: 'https://example.com/com-tam.jpg',
    category: 'RICE',
    lat: 10.7725,
    lng: 106.6945,
};

describe('OrderModal', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('tạo đơn COD thành công và hiển thị mã đơn hàng', async () => {
        const onOrderSuccess = vi.fn();
        vi.mocked(orderService.createRescueOrder).mockResolvedValue({
            id: 'order-1',
            order_code: 'EB-20261126-ABCD',
            consumer_id: 'u1',
            store_id: 's1',
            dish_id: 'dish-101',
            quantity: 2,
            unit_price: 30000,
            total_amount: 60000,
            payment_method: 'COD',
            payment_status: 'PENDING',
            status: 'CONFIRMED',
            co2_saved_kg: 5,
            green_points_earned: 50,
            pickup_deadline: '2026-11-26T21:00:00Z',
            created_at: '2026-11-26T18:00:00Z',
        });

        render(
            <OrderModal
                dish={MOCK_DISH}
                onClose={vi.fn()}
                onOrderSuccess={onOrderSuccess}
            />
        );

        fireEvent.click(screen.getByText('+'));
        fireEvent.click(screen.getByText('Xác nhận cứu món'));

        await waitFor(() => {
            expect(orderService.createRescueOrder).toHaveBeenCalledWith({
                dish_id: 'dish-101',
                quantity: 2,
                payment_method: 'COD',
            });
        });

        expect(await screen.findByText('Đặt đơn giải cứu thành công!')).toBeInTheDocument();
        expect(screen.getByText('EB-20261126-ABCD')).toBeInTheDocument();
        expect(onOrderSuccess).toHaveBeenCalledWith('dish-101', 2);
    });

    it('chuyển sang VNPay sẽ gọi tạo URL thanh toán sau khi tạo đơn', async () => {
        vi.mocked(orderService.createRescueOrder).mockResolvedValue({
            id: 'order-vnpay-1',
            order_code: 'EB-20261126-VNP1',
            consumer_id: 'u1',
            store_id: 's1',
            dish_id: 'dish-101',
            quantity: 1,
            unit_price: 30000,
            total_amount: 30000,
            payment_method: 'VNPAY',
            payment_status: 'PENDING',
            status: 'CONFIRMED',
            co2_saved_kg: 2.5,
            green_points_earned: 25,
            pickup_deadline: '2026-11-26T21:00:00Z',
            created_at: '2026-11-26T18:00:00Z',
        });

        vi.mocked(paymentService.createVnpayUrl).mockResolvedValue({
            payment_url: '#vnpay-sandbox-redirect',
            txn_ref: 'TXN-001',
        });

        render(<OrderModal dish={MOCK_DISH} onClose={vi.fn()} />);

        fireEvent.click(screen.getByText('VNPay Sandbox'));
        fireEvent.click(screen.getByText('Đặt & Thanh toán VNPay'));

        await waitFor(() => {
            expect(orderService.createRescueOrder).toHaveBeenCalledWith({
                dish_id: 'dish-101',
                quantity: 1,
                payment_method: 'VNPAY',
            });
            expect(paymentService.createVnpayUrl).toHaveBeenCalledWith('order-vnpay-1');
        });
    });

    it('hiển thị màn hình hết suất khi backend trả lỗi 409 Conflict', async () => {
        vi.mocked(orderService.createRescueOrder).mockRejectedValue({
            response: { status: 409 },
        });

        render(<OrderModal dish={MOCK_DISH} onClose={vi.fn()} />);

        fireEvent.click(screen.getByText('Xác nhận cứu món'));

        expect(
            await screen.findByText('Rất tiếc, món ăn vừa hết suất!')
        ).toBeInTheDocument();
    });
});