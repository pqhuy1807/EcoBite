import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ReviewModal } from '@/components/ReviewModal';
import { reviewService } from '@/services/review.service';
import type { ReviewResponse } from '@/types/api';

vi.mock('@/services/review.service', () => ({
    reviewService: {
        createReview: vi.fn(),
        createOrderReview: vi.fn(),
        getStoreReviews: vi.fn(),
        listStoreReviews: vi.fn(),
    },
}));

function makeReviewResponse(overrides: Partial<ReviewResponse> = {}): ReviewResponse {
    return {
        id: 'rev-test-1',
        order_id: 'order-123',
        consumer_id: 'consumer-1',
        store_id: 'store-1',
        dish_id: 'dish-1',
        rating: 5,
        comment: 'Món ăn rất ngon, phục vụ chu đáo',
        tags: ['Món ăn ngon', 'Đúng giờ'],
        photo_urls: [],
        created_at: '2026-11-28T14:00:00Z',
        ...overrides,
    };
}

describe('ReviewModal Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('render đúng giao diện ban đầu khi mở modal với order_code và dish_name', () => {
        render(
            <ReviewModal
                isOpen={true}
                onClose={vi.fn()}
                orderId="order-123"
                orderCode="EB-20261128-0001"
                dishName="Cơm Tấm Sườn Bì Chả"
            />
        );

        expect(screen.getByText('Đánh giá món ăn giải cứu')).toBeInTheDocument();
        expect(screen.getByText('EB-20261128-0001')).toBeInTheDocument();
        expect(screen.getByText('Cơm Tấm Sườn Bì Chả')).toBeInTheDocument();
        expect(screen.getByText('Mức độ hài lòng của bạn')).toBeInTheDocument();
        expect(screen.getByText('Rất hài lòng, tuyệt vời (5/5)')).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Hãy chia sẻ cảm nhận của bạn/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Gửi đánh giá' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Hủy' })).toBeInTheDocument();
    });

    it('không render nội dung khi isOpen = false', () => {
        render(
            <ReviewModal
                isOpen={false}
                onClose={vi.fn()}
                orderId="order-123"
            />
        );

        expect(screen.queryByText('Đánh giá món ăn giải cứu')).not.toBeInTheDocument();
    });

    it('cho phép chọn rating từ 1 đến 5 sao và cập nhật mô tả tương ứng', () => {
        render(
            <ReviewModal
                isOpen={true}
                onClose={vi.fn()}
                orderId="order-123"
            />
        );

        // Click star 3
        const star3 = screen.getByRole('button', { name: '3 sao' });
        fireEvent.click(star3);
        expect(screen.getByText('Bình thường (3/5)')).toBeInTheDocument();

        // Click star 1
        const star1 = screen.getByRole('button', { name: '1 sao' });
        fireEvent.click(star1);
        expect(screen.getByText('Rất không hài lòng (1/5)')).toBeInTheDocument();

        // Click star 4
        const star4 = screen.getByRole('button', { name: '4 sao' });
        fireEvent.click(star4);
        expect(screen.getByText('Hài lòng (4/5)')).toBeInTheDocument();
    });

    it('cho phép nhập nội dung nhận xét chi tiết và chọn các thẻ đánh giá nhanh', () => {
        render(
            <ReviewModal
                isOpen={true}
                onClose={vi.fn()}
                orderId="order-123"
            />
        );

        const textarea = screen.getByPlaceholderText(/Hãy chia sẻ cảm nhận của bạn/i);
        fireEvent.change(textarea, { target: { value: 'Suất ăn đóng gói cẩn thận, sườn nóng mềm ngon.' } });
        expect(textarea).toHaveValue('Suất ăn đóng gói cẩn thận, sườn nóng mềm ngon.');

        // Chọn tag nhanh
        const tag1 = screen.getByRole('button', { name: 'Món ăn ngon' });
        fireEvent.click(tag1);

        const tag2 = screen.getByRole('button', { name: 'Đóng gói cẩn thận' });
        fireEvent.click(tag2);

        // Bỏ chọn tag1
        fireEvent.click(tag1);
    });

    it('submit gọi đúng reviewService.createReview với order_id và payload chính xác', async () => {
        const mockSuccess = vi.fn();
        const expectedResponse = makeReviewResponse({
            rating: 4,
            comment: 'Giao nhanh, đồ ăn ngon',
            tags: ['Đúng giờ', 'Món ăn ngon'],
        });
        vi.mocked(reviewService.createReview).mockResolvedValue(expectedResponse);

        render(
            <ReviewModal
                isOpen={true}
                onClose={vi.fn()}
                orderId="order-test-888"
                onSuccess={mockSuccess}
            />
        );

        // Chọn 4 sao
        fireEvent.click(screen.getByRole('button', { name: '4 sao' }));

        // Chọn tags
        fireEvent.click(screen.getByRole('button', { name: 'Đúng giờ' }));
        fireEvent.click(screen.getByRole('button', { name: 'Món ăn ngon' }));

        // Nhập comment
        const textarea = screen.getByPlaceholderText(/Hãy chia sẻ cảm nhận của bạn/i);
        fireEvent.change(textarea, { target: { value: 'Giao nhanh, đồ ăn ngon' } });

        // Submit form
        fireEvent.click(screen.getByRole('button', { name: 'Gửi đánh giá' }));

        await waitFor(() => {
            expect(reviewService.createReview).toHaveBeenCalledWith('order-test-888', {
                rating: 4,
                comment: 'Giao nhanh, đồ ăn ngon',
                tags: ['Đúng giờ', 'Món ăn ngon'],
                photo_urls: [],
            });
        });

        // Hiển thị trạng thái thành công
        expect(await screen.findByText('Cảm ơn đánh giá của bạn!')).toBeInTheDocument();
        expect(mockSuccess).toHaveBeenCalledWith(expectedResponse);
    });

    it('hiển thị trạng thái loading khi đang submit đánh giá', async () => {
        let resolvePromise: (val: ReviewResponse) => void = () => {};
        const pendingPromise = new Promise<ReviewResponse>((resolve) => {
            resolvePromise = resolve;
        });
        vi.mocked(reviewService.createReview).mockReturnValue(pendingPromise);

        render(
            <ReviewModal
                isOpen={true}
                onClose={vi.fn()}
                orderId="order-123"
            />
        );

        const submitBtn = screen.getByRole('button', { name: 'Gửi đánh giá' });
        fireEvent.click(submitBtn);

        // Khi đang submit, nút bị disabled
        await waitFor(() => {
            expect(submitBtn).toBeDisabled();
        });

        // Resolve promise
        resolvePromise(makeReviewResponse());
        expect(await screen.findByText('Cảm ơn đánh giá của bạn!')).toBeInTheDocument();
    });

    it('hiển thị thông báo lỗi API thông thường khi request thất bại', async () => {
        vi.mocked(reviewService.createReview).mockRejectedValue(new Error('Máy chủ gặp sự cố 500'));

        render(
            <ReviewModal
                isOpen={true}
                onClose={vi.fn()}
                orderId="order-123"
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'Gửi đánh giá' }));

        expect(await screen.findByText(/Máy chủ gặp sự cố 500/i)).toBeInTheDocument();
        expect(screen.queryByText('Cảm ơn đánh giá của bạn!')).not.toBeInTheDocument();
    });

    it('xử lý HTTP 409 Conflict một cách thân thiện khi đơn hàng đã được đánh giá trước đó', async () => {
        const conflictError = new axios.AxiosError('Conflict', 'ERR_BAD_REQUEST', undefined, undefined, {
            status: 409,
            statusText: 'Conflict',
            data: { detail: 'Đơn hàng này đã được đánh giá trước đó. Cảm ơn bạn!' },
            headers: {},
            config: {} as any,
        });
        vi.mocked(reviewService.createReview).mockRejectedValue(conflictError);

        render(
            <ReviewModal
                isOpen={true}
                onClose={vi.fn()}
                orderId="order-conflict-123"
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'Gửi đánh giá' }));

        expect(await screen.findByText('Đơn hàng này đã được đánh giá trước đó. Cảm ơn bạn!')).toBeInTheDocument();
        expect(screen.queryByText('Cảm ơn đánh giá của bạn!')).not.toBeInTheDocument();
    });
});
