import { apiClient } from '@/lib/api-client';

export interface SurplusDishResponse {
    id: string;
    store_id: string;
    menu_item_id: string;
    name: string;
    description?: string | null;
    category: string;
    image_url?: string | null;
    original_price: number;
    discounted_price: number;
    discount_percent: number;
    initial_quantity: number;
    remaining_quantity: number;
    pickup_start_time: string;
    pickup_end_time: string;
    rule_discount_start_time?: string | null;
    allergens?: string[];
    status?: string;
}

export interface DishPublishPayload {
    menu_item_id: string;
    quantity: number;
    pickup_start_time: string;
    pickup_end_time: string;
    rule_discount_start_time?: string | null;
}

interface ActiveStoreDishesResponse {
    store_id: string;
    dishes: SurplusDishResponse[];
}

interface UpdateQuantityResponse {
    dish_id?: string;
    id?: string;
    remaining_quantity: number;
    message: string;
}

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

    async updateDishQuantity(
        dishId: string,
        quantity: number
    ): Promise<UpdateQuantityResponse> {
        const { data } = await apiClient.patch<UpdateQuantityResponse>(
            `/dishes/${dishId}/quantity`,
            { quantity }
        );
        return data;
    },
};