import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '@/lib/api-client';
import { reviewService } from '@/services/review.service';

vi.mock('@/lib/api-client', () => ({
    apiClient: {
        get: vi.fn(),
        post: vi.fn(),
    },
}));

describe('reviewService', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('gửi đánh giá đơn hàng COMPLETED đúng endpoint và payload', async () => {
        const payload = {
            rating: 5,
            comment: 'Đồ ăn còn nóng, chủ quán thân thiện',
            tags: ['Ngon', 'Đúng giờ'],
            photo_urls: [],
        };
        vi.mocked(apiClient.post).mockResolvedValue({
            data: {
                id: 'rev-1',
                order_id: 'order-99',
                consumer_id: 'u1',
                store_id: 's1',
                dish_id: 'd1',
                created_at: '2026-11-26T12:00:00Z',
                ...payload,
            },
        });

        const res = await reviewService.createOrderReview('order-99', payload);

        expect(apiClient.post).toHaveBeenCalledWith('/orders/order-99/review', payload);
        expect(res.rating).toBe(5);
    });

    it('lấy danh sách đánh giá cửa hàng kèm phân trang skip/limit', async () => {
        vi.mocked(apiClient.get).mockResolvedValue({ data: [] });

        await reviewService.listStoreReviews('store-1', 10, 20);

        expect(apiClient.get).toHaveBeenCalledWith('/stores/store-1/reviews', {
            params: { skip: 10, limit: 20 },
        });
    });
});