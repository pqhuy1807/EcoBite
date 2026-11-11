import { apiClient } from '@/lib/api-client';

export type DishCategory = 'ALL' | 'RICE' | 'NOODLES' | 'BAKERY' | 'VEGETARIAN';

export interface Dish {
    id: string;
    store_id: string;
    name: string;
    description?: string;
    original_price: number;
    discounted_price: number;
    discount_rate: number; // 0.5 (50%) hoặc 0.7 (70%)
    remaining_quantity: number;
    category: Exclude<DishCategory, 'ALL'>;
    pickup_start_time: string;
    pickup_end_time: string;
    image_url?: string;
}

export const dishService = {
    async getActiveDishes(category?: DishCategory): Promise<Dish[]> {
        const query = category && category !== 'ALL' ? { category } : {};
        const { data } = await apiClient.get<Dish[]>('/dishes', { params: query });
        return data;
    },

    async getDishById(id: string): Promise<Dish> {
        const { data } = await apiClient.get<Dish>(`/dishes/${id}`);
        return data;
    },
};