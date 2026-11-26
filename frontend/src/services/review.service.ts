import { apiClient } from '@/lib/api-client';
import type { ReviewCreatePayload, ReviewResponse } from '@/types/api';

export const reviewService = {
    async createOrderReview(
        orderId: string,
        payload: ReviewCreatePayload
    ): Promise<ReviewResponse> {
        const { data } = await apiClient.post<ReviewResponse>(
            `/orders/${orderId}/review`,
            payload
        );
        return data;
    },

    async listStoreReviews(
        storeId: string,
        skip = 0,
        limit = 20
    ): Promise<ReviewResponse[]> {
        const { data } = await apiClient.get<ReviewResponse[]>(
            `/stores/${storeId}/reviews`,
            { params: { skip, limit } }
        );
        return data;
    },
};