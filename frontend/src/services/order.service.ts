import { apiClient } from '@/lib/api-client';

export interface CreateOrderPayload {
    dish_id: string;
    quantity: number;
}

export interface OrderResponse {
    id: string;
    order_code: string; // VD: EB-20261109-XXXX
    status: 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'EXPIRED';
    quantity: number;
    total_price: number;
    co2_saved_kg: number;
    green_points: number;
    pickup_deadline: string;
}

export const orderService = {
    async createRescueOrder(payload: CreateOrderPayload): Promise<OrderResponse> {
        const { data } = await apiClient.post<OrderResponse>('/orders', payload);
        return data;
    },

    async cancelOrder(orderId: string): Promise<OrderResponse> {
        const { data } = await apiClient.patch<OrderResponse>(`/orders/${orderId}/cancel`);
        return data;
    },

    async getMyOrders(): Promise<OrderResponse[]> {
        const { data } = await apiClient.get<OrderResponse[]>('/orders/me');
        return data;
    },
};