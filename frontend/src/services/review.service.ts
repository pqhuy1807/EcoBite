import { apiClient } from '@/lib/api-client';
import type { ReviewCreatePayload, ReviewResponse } from '@/types/api';

export const reviewService = {
    async createReview(
        orderId: string,
        payload: ReviewCreatePayload
    ): Promise<ReviewResponse> {
        const { data } = await apiClient.post<ReviewResponse>(
            `/orders/${orderId}/review`,
            payload
        );
        return data;
    },

    async createOrderReview(
        orderId: string,
        payload: ReviewCreatePayload
    ): Promise<ReviewResponse> {
        return this.createReview(orderId, payload);
    },

    async getStoreReviews(
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

    async listStoreReviews(
        storeId: string,
        skip = 0,
        limit = 20
    ): Promise<ReviewResponse[]> {
        return this.getStoreReviews(storeId, skip, limit);
    },
};
