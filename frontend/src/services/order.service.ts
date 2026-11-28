import { apiClient } from '@/lib/api-client';
import {
    CreateOrderPayload,
    OrderDetailResponse,
    OrderResponse,
    OrderStatus,
    QRPayloadResponse,
    QRVerificationResponse,
} from '@/types/api';

export type {
    CreateOrderPayload,
    OrderDetailResponse,
    OrderResponse,
    OrderStatus,
    QRPayloadResponse,
    QRVerificationResponse,
};

export const orderService = {
    async createRescueOrder(
        payload: CreateOrderPayload
    ): Promise<OrderResponse> {
        const { data } = await apiClient.post<OrderResponse>('/orders', {
            dish_id: payload.dish_id,
            quantity: payload.quantity,
            payment_method: payload.payment_method ?? 'COD',
        });
        return data;
    },

    async cancelOrder(orderId: string): Promise<OrderResponse> {
        const { data } = await apiClient.patch<OrderResponse>(
            `/orders/${orderId}/cancel`
        );
        return data;
    },

    async getMyOrders(status?: OrderStatus): Promise<OrderResponse[]> {
        const { data } = await apiClient.get<OrderResponse[]>('/orders/me', {
            params: status ? { status } : undefined,
        });
        return data;
    },

    async getStoreOrders(
        storeId: string,
        status?: OrderStatus
    ): Promise<OrderResponse[]> {
        const { data } = await apiClient.get<OrderResponse[]>(
            `/orders/store/${storeId}`,
            {
                params: status ? { status } : undefined,
            }
        );
        return data;
    },

    async getOrderDetail(orderId: string): Promise<OrderDetailResponse> {
        const { data } = await apiClient.get<OrderDetailResponse>(
            `/orders/${orderId}`
        );
        return data;
    },

    async issueOrderQr(orderId: string): Promise<QRPayloadResponse> {
        const { data } = await apiClient.post<QRPayloadResponse>(
            `/orders/${orderId}/qr`
        );
        return data;
    },

    async verifyOrderQr(qrToken: string): Promise<QRVerificationResponse> {
        const { data } = await apiClient.post<QRVerificationResponse>(
            '/orders/verify-qr',
            { qr_token: qrToken }
        );
        return data;
    },
};