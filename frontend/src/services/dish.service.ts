import { apiClient } from '@/lib/api-client';
import type {
    ActiveStoreDishesResponse,
    DishBatchPublishPayload,
    DishPublishPayload,
    SurplusDishResponse,
    UpdateDishQuantityResponse,
} from '@/types/api';

export type DishCategory = 'ALL' | 'RICE' | 'NOODLES' | 'BAKERY' | 'VEGETARIAN';
export type Dish = SurplusDishResponse;

export const dishService = {
    async getActiveStoreDishes(storeId: string): Promise<SurplusDishResponse[]> {
        const { data } = await apiClient.get<ActiveStoreDishesResponse>(
            `/stores/${storeId}/dishes/active`
        );
        return data.dishes;
    },

    async createSurplusDish(
        payload: DishPublishPayload
    ): Promise<SurplusDishResponse> {
        const { data } = await apiClient.post<SurplusDishResponse>(
            '/dishes',
            payload
        );
        return data;
    },

    async batchCreateSurplusDishes(
        payload: DishBatchPublishPayload
    ): Promise<{ created_count: number; dishes: SurplusDishResponse[] }> {
        const { data } = await apiClient.post<{
            created_count: number;
            dishes: SurplusDishResponse[];
        }>('/dishes/batch', payload);
        return data;
    },

    async updateDishQuantity(
        dishId: string,
        quantity: number
    ): Promise<UpdateDishQuantityResponse> {
        const { data } = await apiClient.patch<UpdateDishQuantityResponse>(
            `/dishes/${dishId}/quantity`,
            { quantity }
        );
        return data;
    },
};