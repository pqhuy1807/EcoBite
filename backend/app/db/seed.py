"""Database seeding script for EcoBite Platform.

Provides rich, realistic sample data matching the business specifications in
docs/01_PRD_and_User_Stories.md, docs/02_System_Architecture.md, and
docs/03_Database_Schema_ERD.md.

Populates 23 realistic F&B stores across 3 key geographical clusters in Ho Chi Minh City:
- Cluster 1: District 1 (Bến Nghé, Đa Kao, Bến Thành) - Business & Tourism Hub
- Cluster 2: District 5 (Chợ Lớn, Nguyễn Tri Phương, Ký Hòa) - Cultural & Culinary Hub
- Cluster 3: TP. Thủ Đức (Làng Đại học ĐHQG, Linh Trung) - Student & Campus Hub

Usage:
    cd backend
    python -m app.db.seed
    # Or with --reset to wipe existing tables and re-create clean sample data:
    python -m app.db.seed --reset
"""

import asyncio
import sys
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.dish import Dish, DishStatus
from app.models.gamification import (
    GreenPointsLedger,
    PointActionType,
    UserVoucher,
    Voucher,
)
from app.models.interaction import Notification, NotificationType, Review
from app.models.menu_item import DietaryType, ItemCategory, MenuItem
from app.models.order import (
    Order,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    PaymentTransaction,
    QRToken,
)
from app.models.store import KycStatus, Store
from app.models.user import DietaryPreference, User, UserPreference, UserRole

DEFAULT_PASSWORD = "Password123!"

# ==============================================================================
# SEED SPECIFICATION: 23 REAL F&B STORES IN HO CHI MINH CITY
# ==============================================================================
STORE_SEEDS_DATA: list[dict[str, Any]] = [
    # --------------------------------------------------------------------------
    # CLUSTER 1: DISTRICT 1 (Bến Nghé, Đa Kao, Bến Thành - Văn phòng & Du lịch)
    # --------------------------------------------------------------------------
    {
        "merchant_email": "merchant.bui@ecobite.vn",
        "merchant_name": "Nguyễn Văn Hùng",
        "phone": "0902000001",
        "name": "Cơm Tấm Bụi Sài Gòn - Hai Bà Trưng",
        "description": "Cơm tấm sườn bì chả nướng than hoa gia truyền nức tiếng trung tâm Quận 1",
        "address": "100 Hai Bà Trưng, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        "location": "POINT(106.7005 10.7792)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
        "rating_avg": Decimal("4.85"),
        "rating_count": 142,
        "total_co2_saved_kg": Decimal("355.00"),
        "menu_items": [
            {
                "name": "Cơm Sườn Bì Chả Nướng Mật Ong",
                "description": "Sườn cốt lết dày ướp mật ong than hoa, chả trứng chưng, bì thơm",
                "category": ItemCategory.RICE,
                "original_price": Decimal("55000.00"),
                "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=600",
                "standard_ingredients": ["Gạo tấm", "Sườn heo", "Trứng", "Bì heo", "Mỡ hành"],
                "base_allergens": ["Eggs (Trứng)", "Fish (Nước mắm)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Cơm Sườn Bì Chả (Ca Trưa Cứu Hộ)",
                    "description": "Suất cơm trưa chất lượng đóng hộp bã mía sạch sẽ giữ nóng",
                    "rescue_price": Decimal("30000.00"),
                    "rule_discount_price": Decimal("16500.00"),
                    "pickup_start_time": time(13, 30),
                    "pickup_end_time": time(15, 30),
                    "total_quantity": 10,
                    "remaining_quantity": 6,
                    "allergens": [
                        {
                            "allergen": "Eggs (Trứng)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Có chả trứng chưng",
                        }
                    ],
                    "dietary_notes": ["Có mỡ hành", "Kèm dưa chua"],
                },
            },
            {
                "name": "Cơm Đùi Gà Nướng Sốt Teriyaki",
                "description": "Đùi gà nướng mềm mọng nước rưới sốt teriyaki thơm lừng",
                "category": ItemCategory.RICE,
                "original_price": Decimal("50000.00"),
                "image_url": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=600",
                "standard_ingredients": ["Gạo tấm", "Đùi gà", "Nước tương", "Mè rang"],
                "base_allergens": ["Gluten", "Sesame (Mè)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Cơm Đùi Gà Nướng (Ca Chiều)",
                    "description": "Gà nướng thơm giòn đậm đà trong ngày",
                    "rescue_price": Decimal("25000.00"),
                    "rule_discount_price": Decimal("15000.00"),
                    "pickup_start_time": time(14, 0),
                    "pickup_end_time": time(16, 0),
                    "total_quantity": 8,
                    "remaining_quantity": 4,
                    "allergens": [
                        {
                            "allergen": "Sesame (Mè)",
                            "risk_level": "LOW",
                            "source": "INFERRED",
                            "reason": "Rắc hạt mè lên sốt",
                        }
                    ],
                    "dietary_notes": ["Ít cay", "Kèm canh rau má"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.huynhhoa@ecobite.vn",
        "merchant_name": "Lê Thị Hoa",
        "phone": "0902000002",
        "name": "Bánh Mì Huỳnh Hoa - Lê Thị Riêng",
        "description": "Thương hiệu bánh mì patê thịt chả trứ danh Sài Gòn ngập tràn topping",
        "address": "26 Lê Thị Riêng, Phường Bến Thành, Quận 1, TP. Hồ Chí Minh",
        "location": "POINT(106.6917 10.7716)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500",
        "rating_avg": Decimal("4.92"),
        "rating_count": 210,
        "total_co2_saved_kg": Decimal("490.00"),
        "menu_items": [
            {
                "name": "Bánh Mì Patê Chả Thịt Nguội Đặc Biệt",
                "description": "Vỏ giòn rụm kẹp 6 loại chả lụa, giò thủ, thịt đỏ, patê gan béo ngậ",
                "category": ItemCategory.BAKERY,
                "original_price": Decimal("65000.00"),
                "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600",
                "standard_ingredients": [
                    "Bột mì",
                    "Patê gan",
                    "Chả lụa",
                    "Giò thủ",
                    "Thịt nguội",
                    "Đồ chua",
                ],
                "base_allergens": ["Gluten", "Soybeans (Đậu nành)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Bánh Mì Huỳnh Hoa Đặc Biệt (Xả Ca Đêm)",
                    "description": "Bánh mì đầy đặn thịt nguội và patê ngon tươi trong ngày",
                    "rescue_price": Decimal("35000.00"),
                    "rule_discount_price": Decimal("19500.00"),
                    "pickup_start_time": time(20, 0),
                    "pickup_end_time": time(22, 0),
                    "total_quantity": 15,
                    "remaining_quantity": 9,
                    "allergens": [
                        {
                            "allergen": "Gluten",
                            "risk_level": "HIGH",
                            "source": "INFERRED",
                            "reason": "Bột mì bánh mì",
                        }
                    ],
                    "dietary_notes": ["Đồ chua để riêng", "Patê béo ngậy"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.coffeehouse@ecobite.vn",
        "merchant_name": "Trần Thanh Phong",
        "phone": "0902000003",
        "name": "The Coffee House - Pasteur",
        "description": "Không gian cà phê sáng tạo với đồ uống pha chế và các loại bánh ngọt tươi",
        "address": "141 Pasteur, Phường Võ Thị Sáu, Quận 3, TP. Hồ Chí Minh",
        "location": "POINT(106.6961 10.7845)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=500",
        "rating_avg": Decimal("4.78"),
        "rating_count": 95,
        "total_co2_saved_kg": Decimal("180.00"),
        "menu_items": [
            {
                "name": "Bánh Mousse Phúc Bồn Tử",
                "description": "Bánh mousse mềm mịn vị chua thanh ngọt dịu của phúc bồn tử tự nhiê",
                "category": ItemCategory.BAKERY,
                "original_price": Decimal("45000.00"),
                "image_url": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=600",
                "standard_ingredients": ["Kem sữa tươi", "Phúc bồn tử", "Bột mì", "Trứng"],
                "base_allergens": ["Milk (Sữa)", "Eggs (Trứng)", "Gluten"],
                "dietary_type": DietaryType.VEGETARIAN,
                "dish": {
                    "name": "Bánh Mousse Phúc Bồn Tử (Cuối Ngày)",
                    "description": "Bánh ngọt tươi bảo quản mát hoàn hảo giải cứu trước giờ đóng c",
                    "rescue_price": Decimal("23000.00"),
                    "rule_discount_price": Decimal("13500.00"),
                    "pickup_start_time": time(20, 30),
                    "pickup_end_time": time(22, 0),
                    "total_quantity": 6,
                    "remaining_quantity": 4,
                    "allergens": [
                        {
                            "allergen": "Milk (Sữa)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Kem bơ sữa",
                        }
                    ],
                    "dietary_notes": ["Ăn chay dùng được", "Bảo quản lạnh"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.katinat@ecobite.vn",
        "merchant_name": "Phạm Quốc Bảo",
        "phone": "0902000004",
        "name": "Katinat Saigon Kafe - Đồng Khởi",
        "description": "Chuỗi đồ uống hiện đại nổi tiếng với các dòng trà trái cây và bánh nướng t",
        "address": "91 Đồng Khởi, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        "location": "POINT(106.7038 10.7745)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1556881286-fc6915169721?w=500",
        "rating_avg": Decimal("4.80"),
        "rating_count": 120,
        "total_co2_saved_kg": Decimal("240.00"),
        "menu_items": [
            {
                "name": "Bánh Sừng Bò Phô Mai Trứng Muối",
                "description": "Bánh croissant ngậy bơ xốp mềm nhân sốt trứng muối sánh mịn",
                "category": ItemCategory.BAKERY,
                "original_price": Decimal("40000.00"),
                "image_url": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=600",
                "standard_ingredients": ["Bột mì", "Bơ Pháp", "Phô mai", "Trứng muối"],
                "base_allergens": ["Gluten", "Milk (Sữa)", "Eggs (Trứng)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Croissant Trứng Muối (Giờ Vàng Chiều)",
                    "description": "Mẻ bánh nướng tươi ngon trong ngày xả ca chiều",
                    "rescue_price": Decimal("22000.00"),
                    "rule_discount_price": Decimal("12000.00"),
                    "pickup_start_time": time(17, 0),
                    "pickup_end_time": time(19, 0),
                    "total_quantity": 10,
                    "remaining_quantity": 5,
                    "allergens": [
                        {
                            "allergen": "Eggs (Trứng)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Nhân trứng muối",
                        }
                    ],
                    "dietary_notes": ["Nhiều bơ thơm"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.pizza4ps@ecobite.vn",
        "merchant_name": "Vũ Đình Tuấn",
        "phone": "0902000005",
        "name": "Pizza 4P's - Lê Thánh Tôn",
        "description": "Nghệ thuật ẩm thực Pizza lò củi thủ công và phô mai tươi tự làm",
        "address": "8/15 Lê Thánh Tôn, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        "location": "POINT(106.7046 10.7801)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500",
        "rating_avg": Decimal("4.96"),
        "rating_count": 320,
        "total_co2_saved_kg": Decimal("780.00"),
        "menu_items": [
            {
                "name": "Pizza Phô Mai Burrata Thịt Nguội",
                "description": "Bánh pizza lò củi thượng hạng phủ phô mai tươi Burrata và thịt heo",
                "category": ItemCategory.OTHER,
                "original_price": Decimal("250000.00"),
                "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600",
                "standard_ingredients": [
                    "Bột mì lên men",
                    "Phô mai Burrata",
                    "Parma Ham",
                    "Cà chua bi",
                    "Lá húng tây",
                ],
                "base_allergens": ["Gluten", "Milk (Sữa)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Pizza Phô Mai Burrata (Suất Giải Cứu)",
                    "description": "Pizza lò củi chuẩn bị cho tiệc tối chưa dùng hết, đóng hộp ngu",
                    "rescue_price": Decimal("125000.00"),
                    "rule_discount_price": Decimal("75000.00"),
                    "pickup_start_time": time(21, 0),
                    "pickup_end_time": time(22, 30),
                    "total_quantity": 4,
                    "remaining_quantity": 2,
                    "allergens": [
                        {
                            "allergen": "Milk (Sữa)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Phô mai tươi",
                        }
                    ],
                    "dietary_notes": ["Nướng củi tự nhiên"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.bepchay@ecobite.vn",
        "merchant_name": "Đặng Thị Mai",
        "phone": "0902000006",
        "name": "Bếp Chay An Lạc - Phạm Hồng Thái",
        "description": "Quán ẩm thực thực dưỡng chay thanh tịnh, bảo vệ sức khỏe và môi trường",
        "address": "32 Phạm Hồng Thái, Phường Bến Thành, Quận 1, TP. Hồ Chí Minh",
        "location": "POINT(106.6935 10.7725)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
        "rating_avg": Decimal("4.88"),
        "rating_count": 110,
        "total_co2_saved_kg": Decimal("310.00"),
        "menu_items": [
            {
                "name": "Cơm Chiên Hạt Sen Ngọc Bích",
                "description": "Cơm chiên lá cẩm hạt sen bùi béo kết hợp nấm đông cô tươi và chả l",
                "category": ItemCategory.VEGETARIAN,
                "original_price": Decimal("45000.00"),
                "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600",
                "standard_ingredients": [
                    "Gạo thơm",
                    "Hạt sen",
                    "Nấm đông cô",
                    "Đậu hà lan",
                    "Cà rốt",
                ],
                "base_allergens": [],
                "dietary_type": DietaryType.VEGAN,
                "dish": {
                    "name": "Cơm Chiên Hạt Sen (Cứu Hộ Cuối Trưa)",
                    "description": "Suất cơm chay bổ dưỡng thanh thuần trong ngày",
                    "rescue_price": Decimal("24000.00"),
                    "rule_discount_price": Decimal("13500.00"),
                    "pickup_start_time": time(13, 0),
                    "pickup_end_time": time(15, 0),
                    "total_quantity": 8,
                    "remaining_quantity": 5,
                    "allergens": [],
                    "dietary_notes": ["Thuần chay (Vegan)", "Không bột ngọt"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.touslesjours@ecobite.vn",
        "merchant_name": "Kim Min Joon",
        "phone": "0902000007",
        "name": "Tous Les Jours - Nguyễn Đình Chiểu",
        "description": "Tiệm bánh phong cách Pháp - Á Á Châu với các mẻ bánh nướng thơm lừng trong",
        "address": "180 Nguyễn Đình Chiểu, Phường Đa Kao, Quận 1, TP. Hồ Chí Minh",
        "location": "POINT(106.6948 10.7852)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500",
        "rating_avg": Decimal("4.82"),
        "rating_count": 89,
        "total_co2_saved_kg": Decimal("195.00"),
        "menu_items": [
            {
                "name": "Bánh Pastry Xúc Xích Phô Mai",
                "description": "Bánh ngàn lớp thơm bơ kẹp xúc xích gà xông khói và sốt mù tạt ngọt",
                "category": ItemCategory.BAKERY,
                "original_price": Decimal("38000.00"),
                "image_url": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=600",
                "standard_ingredients": ["Bột mì", "Bơ lạt", "Xúc xích gà", "Phô mai"],
                "base_allergens": ["Gluten", "Milk (Sữa)", "Mustard (Mù tạt)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Pastry Xúc Xích Phô Mai (Ca Chiều)",
                    "description": "Bánh nóng giòn nướng trong ngày",
                    "rescue_price": Decimal("20000.00"),
                    "rule_discount_price": Decimal("11400.00"),
                    "pickup_start_time": time(17, 30),
                    "pickup_end_time": time(19, 30),
                    "total_quantity": 12,
                    "remaining_quantity": 7,
                    "allergens": [
                        {
                            "allergen": "Gluten",
                            "risk_level": "HIGH",
                            "source": "INFERRED",
                            "reason": "Bột lúa mì",
                        }
                    ],
                    "dietary_notes": ["Ăn liền giòn ngon"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.phohoa@ecobite.vn",
        "merchant_name": "Võ Thị Thanh",
        "phone": "0902000008",
        "name": "Phở Hòa Pasteur - Đa Kao",
        "description": "Thương hiệu phở truyền thống lâu đời với nước dùng hầm xương tủy bò 18 tiế",
        "address": "260C Pasteur, Phường Võ Thị Sáu, Quận 3, TP. Hồ Chí Minh",
        "location": "POINT(106.6890 10.7895)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=500",
        "rating_avg": Decimal("4.87"),
        "rating_count": 178,
        "total_co2_saved_kg": Decimal("410.00"),
        "menu_items": [
            {
                "name": "Phở Bò Tái Nạm Gầu Bò",
                "description": "Bánh phở mềm dai, thịt bò hoa tươi tái ngọt, gầu giòn và nước dùng",
                "category": ItemCategory.NOODLES,
                "original_price": Decimal("75000.00"),
                "image_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=600",
                "standard_ingredients": [
                    "Bánh phở gạo",
                    "Thịt bò tái",
                    "Nạm bò",
                    "Hành hoa",
                    "Rau quế",
                ],
                "base_allergens": ["Fish (Nước mắm)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Phở Bò Nạm Gầu (Ca Tối Muộn)",
                    "description": "Nước dùng phở đóng túi giữ nhiệt riêng, bánh phở tươi kèm thịt",
                    "rescue_price": Decimal("40000.00"),
                    "rule_discount_price": Decimal("22500.00"),
                    "pickup_start_time": time(21, 0),
                    "pickup_end_time": time(22, 30),
                    "total_quantity": 8,
                    "remaining_quantity": 5,
                    "allergens": [
                        {
                            "allergen": "Fish (Nước mắm)",
                            "risk_level": "LOW",
                            "source": "INFERRED",
                            "reason": "Nêm nước mắm",
                        }
                    ],
                    "dietary_notes": ["Nhiều hành ngò", "Nước dùng nóng hổi"],
                },
            },
        ],
    },
    # --------------------------------------------------------------------------
    # CLUSTER 2: DISTRICT 5 (Chợ Lớn, Nguyễn Tri Phương, Ký Hòa - Văn hóa Ẩm thực)
    # --------------------------------------------------------------------------
    {
        "merchant_email": "merchant.cacan@ecobite.vn",
        "merchant_name": "Lâm Quốc Trọng",
        "phone": "0903000001",
        "name": "Hủ Tiếu Cả Cần - Hùng Vương Chợ Lớn",
        "description": "Hủ tiếu sườn tôm khô và bánh bao xá xíu nổi danh hơn nửa thế kỷ khu Chợ Lớ",
        "address": "110 Hùng Vương, Phường 9, Quận 5, TP. Hồ Chí Minh",
        "location": "POINT(106.6698 10.7583)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=500",
        "rating_avg": Decimal("4.90"),
        "rating_count": 240,
        "total_co2_saved_kg": Decimal("520.00"),
        "menu_items": [
            {
                "name": "Hủ Tiếu Mì Sườn Non Tôm Tươi",
                "description": "Sợi hủ tiếu dai tẩm sốt tương đen đặc trưng, sườn non hầm rục và t",
                "category": ItemCategory.NOODLES,
                "original_price": Decimal("65000.00"),
                "image_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=600",
                "standard_ingredients": [
                    "Sợi hủ tiếu",
                    "Sợi mì trứng",
                    "Sườn heo",
                    "Tôm",
                    "Tỏi phi",
                ],
                "base_allergens": ["Crustaceans (Tôm)", "Eggs (Trứng)", "Gluten"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Hủ Tiếu Sườn Tôm Cả Cần (Ca Chiều)",
                    "description": "Suất hủ tiếu trọn vẹn chất lượng ngon đúng chuẩn",
                    "rescue_price": Decimal("35000.00"),
                    "rule_discount_price": Decimal("19500.00"),
                    "pickup_start_time": time(14, 0),
                    "pickup_end_time": time(16, 0),
                    "total_quantity": 10,
                    "remaining_quantity": 6,
                    "allergens": [
                        {
                            "allergen": "Crustaceans (Tôm)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Có tôm sú tươi",
                        }
                    ],
                    "dietary_notes": ["Tỏi phi thơm nồng"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.thophat@ecobite.vn",
        "merchant_name": "Lý Gia Hào",
        "phone": "0903000002",
        "name": "Bánh Bao Thọ Phát - Nguyễn Tri Phương",
        "description": "Xưởng bánh bao, há cảo và xíu mại dimsum truyền thống người Hoa",
        "address": "78 Nguyễn Tri Phương, Phường 7, Quận 5, TP. Hồ Chí Minh",
        "location": "POINT(106.6685 10.7547)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=500",
        "rating_avg": Decimal("4.85"),
        "rating_count": 190,
        "total_co2_saved_kg": Decimal("380.00"),
        "menu_items": [
            {
                "name": "Bánh Bao Hoàng Kim Trứng Chảy",
                "description": "Vỏ bánh trắng mịn xốp mềm, nhân kim sa trứng muối béo ngậy ngọt dị",
                "category": ItemCategory.BAKERY,
                "original_price": Decimal("20000.00"),
                "image_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=600",
                "standard_ingredients": ["Bột mì", "Trứng muối", "Bơ sữa", "Sữa đặc"],
                "base_allergens": ["Gluten", "Eggs (Trứng)", "Milk (Sữa)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Bánh Bao Hoàng Kim (Hộp 4 Cái)",
                    "description": "Bánh hấp mới trong ngày thơm ngậy",
                    "rescue_price": Decimal("40000.00"),
                    "rule_discount_price": Decimal("24000.00"),
                    "pickup_start_time": time(18, 0),
                    "pickup_end_time": time(20, 0),
                    "total_quantity": 8,
                    "remaining_quantity": 4,
                    "allergens": [
                        {
                            "allergen": "Eggs (Trứng)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Nhân trứng muối",
                        }
                    ],
                    "dietary_notes": ["Ăn nóng ngon nhất"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.dongnguyen@ecobite.vn",
        "merchant_name": "Lương Kiến Phát",
        "phone": "0903000003",
        "name": "Cơm Gà Đông Nguyên - Nguyễn Trãi",
        "description": "Quán cơm gà Hải Nam da giòn thịt ngọt nước sốt gừng tương đen nức danh Chợ",
        "address": "801 Nguyễn Trãi, Phường 14, Quận 5, TP. Hồ Chí Minh",
        "location": "POINT(106.6575 10.7522)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=500",
        "rating_avg": Decimal("4.89"),
        "rating_count": 160,
        "total_co2_saved_kg": Decimal("390.00"),
        "menu_items": [
            {
                "name": "Cơm Gà Luộc Da Vàng Chợ Lớn",
                "description": "Thịt gà thả vườn da giòn bóng bẩy, cơm nấu nước luộc gà hạt óng mỡ",
                "category": ItemCategory.RICE,
                "original_price": Decimal("65000.00"),
                "image_url": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=600",
                "standard_ingredients": [
                    "Gạo tám thơm",
                    "Thịt gà ta",
                    "Gừng",
                    "Tỏi phi",
                    "Nước tương ngọt",
                ],
                "base_allergens": ["Soybeans (Đậu nành)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Cơm Gà Luộc (Ca Chiều Muộn)",
                    "description": "Cơm gà thơm ngon béo ngậy kèm dưa chuột sốt gừng",
                    "rescue_price": Decimal("35000.00"),
                    "rule_discount_price": Decimal("19500.00"),
                    "pickup_start_time": time(14, 30),
                    "pickup_end_time": time(16, 30),
                    "total_quantity": 7,
                    "remaining_quantity": 4,
                    "allergens": [
                        {
                            "allergen": "Soybeans (Đậu nành)",
                            "risk_level": "LOW",
                            "source": "INFERRED",
                            "reason": "Sốt nước tương",
                        }
                    ],
                    "dietary_notes": ["Kèm sốt gừng ớt"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.tienphat@ecobite.vn",
        "merchant_name": "Lưu Thiếu Khang",
        "phone": "0903000004",
        "name": "Dimsum Tiến Phát - Ký Hòa",
        "description": "Điểm tâm sáng và trưa kiểu Quảng Đông truyền thống chuẩn vị người Hoa",
        "address": "18 Ký Hòa, Phường 11, Quận 5, TP. Hồ Chí Minh",
        "location": "POINT(106.6621 10.7538)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=500",
        "rating_avg": Decimal("4.87"),
        "rating_count": 130,
        "total_co2_saved_kg": Decimal("280.00"),
        "menu_items": [
            {
                "name": "Xíu Mại Tôm Thịt & Há Cảo Sò Điệp",
                "description": "Xíu mại nặn tay thịt ngọt tươi, há cảo sò điệp hấp trong xửng tre",
                "category": ItemCategory.OTHER,
                "original_price": Decimal("50000.00"),
                "image_url": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=600",
                "standard_ingredients": ["Tôm sú", "Thịt nạc vai", "Sò điệp", "Bột gạo", "Dầu mè"],
                "base_allergens": ["Crustaceans (Tôm)", "Molluscs (Sò)", "Sesame (Mè)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Combo Dimsum 6 Viên (Cuối Giờ Trưa)",
                    "description": "Các món dimsum nóng trong ngày xả ca trưa",
                    "rescue_price": Decimal("27000.00"),
                    "rule_discount_price": Decimal("15000.00"),
                    "pickup_start_time": time(13, 0),
                    "pickup_end_time": time(14, 30),
                    "total_quantity": 10,
                    "remaining_quantity": 5,
                    "allergens": [
                        {
                            "allergen": "Crustaceans (Tôm)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Nhân tôm thịt",
                        }
                    ],
                    "dietary_notes": ["Kèm giấm đỏ Tiều Châu"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.tienhuong@ecobite.vn",
        "merchant_name": "Chu Cẩm Lệ",
        "phone": "0903000005",
        "name": "Trà Sữa Tiên Hưởng - Trần Hưng Đạo",
        "description": "Thương hiệu trà sữa lá trà tươi tự nhiên Đài Loan thanh mát tại Quận 5",
        "address": "940 Trần Hưng Đạo, Phường 7, Quận 5, TP. Hồ Chí Minh",
        "location": "POINT(106.6712 10.7541)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1556881286-fc6915169721?w=500",
        "rating_avg": Decimal("4.75"),
        "rating_count": 80,
        "total_co2_saved_kg": Decimal("150.00"),
        "menu_items": [
            {
                "name": "Trà Sữa Oolong Nướng Trân Châu Hoàng Kim",
                "description": "Lá trà Oolong rang đậm vị hòa cùng sữa béo và trân châu mật ong dẻ",
                "category": ItemCategory.BEVERAGE,
                "original_price": Decimal("42000.00"),
                "image_url": "https://images.unsplash.com/photo-1556881286-fc6915169721?w=600",
                "standard_ingredients": [
                    "Cốt trà Oolong",
                    "Bột sữa",
                    "Trân châu hoàng kim",
                    "Mật ong",
                ],
                "base_allergens": ["Milk (Sữa)"],
                "dietary_type": DietaryType.VEGETARIAN,
                "dish": {
                    "name": "Trà Sữa Oolong (Ca Tối)",
                    "description": "Trà sữa pha tươi đậm đà giảm giá cứu hộ",
                    "rescue_price": Decimal("22000.00"),
                    "rule_discount_price": Decimal("12600.00"),
                    "pickup_start_time": time(20, 0),
                    "pickup_end_time": time(21, 30),
                    "total_quantity": 10,
                    "remaining_quantity": 6,
                    "allergens": [
                        {
                            "allergen": "Milk (Sữa)",
                            "risk_level": "MEDIUM",
                            "source": "EXPLICIT",
                            "reason": "Sữa béo",
                        }
                    ],
                    "dietary_notes": ["Độ ngọt 50%", "Đá riêng"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.batnha@ecobite.vn",
        "merchant_name": "Sư Cô Tâm An",
        "phone": "0903000006",
        "name": "Quán Cơm Chay Bát Nhã - An Dương Vương",
        "description": "Cơm chay bình dân bổ dưỡng phục vụ sinh viên và người dân lao động Quận 5",
        "address": "218 An Dương Vương, Phường 4, Quận 5, TP. Hồ Chí Minh",
        "location": "POINT(106.6792 10.7578)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
        "rating_avg": Decimal("4.91"),
        "rating_count": 150,
        "total_co2_saved_kg": Decimal("360.00"),
        "menu_items": [
            {
                "name": "Cơm Tấm Chả Nấm Đậu Hũ Chay",
                "description": "Cơm tấm gạo thơm, chả nấm mộc nhĩ đậu hũ nướng, sườn non chay rim",
                "category": ItemCategory.VEGETARIAN,
                "original_price": Decimal("35000.00"),
                "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600",
                "standard_ingredients": ["Gạo tấm", "Đậu hũ", "Nấm rơm", "Mộc nhĩ", "Tàu hũ ky"],
                "base_allergens": ["Soybeans (Đậu nành)"],
                "dietary_type": DietaryType.VEGAN,
                "dish": {
                    "name": "Cơm Tấm Chay An Lạc (Cuối Trưa)",
                    "description": "Suất cơm chay thơm ngon đầy đặn giải cứu trưa muộn",
                    "rescue_price": Decimal("18000.00"),
                    "rule_discount_price": Decimal("10500.00"),
                    "pickup_start_time": time(13, 30),
                    "pickup_end_time": time(15, 0),
                    "total_quantity": 12,
                    "remaining_quantity": 8,
                    "allergens": [
                        {
                            "allergen": "Soybeans (Đậu nành)",
                            "risk_level": "LOW",
                            "source": "INFERRED",
                            "reason": "Sườn non đậu nành",
                        }
                    ],
                    "dietary_notes": ["Thuần chay", "Kèm canh rong biển"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.haky@ecobite.vn",
        "merchant_name": "Hà Vĩnh Sanh",
        "phone": "0903000007",
        "name": "Quán Chè Hà Ký - Châu Văn Liêm",
        "description": "Thiên đường chè Hoa truyền thống với quy linh cao, chè mè đen, chè hạt sen",
        "address": "138 Châu Văn Liêm, Phường 11, Quận 5, TP. Hồ Chí Minh",
        "location": "POINT(106.6582 10.7511)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=500",
        "rating_avg": Decimal("4.84"),
        "rating_count": 92,
        "total_co2_saved_kg": Decimal("170.00"),
        "menu_items": [
            {
                "name": "Chè Mè Đen Hạnh Nhân Nóng",
                "description": "Mè đen xay nhuyễn béo bùi, hương hạnh nhân thơm nhẹ, bổ dưỡng cho",
                "category": ItemCategory.OTHER,
                "original_price": Decimal("28000.00"),
                "image_url": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=600",
                "standard_ingredients": ["Mè đen", "Hạnh nhân", "Đường phèn", "Bột sắn dây"],
                "base_allergens": ["Sesame (Mè)", "Nuts (Quả hạch)"],
                "dietary_type": DietaryType.VEGAN,
                "dish": {
                    "name": "Chè Mè Đen Hạnh Nhân (Ca Đêm)",
                    "description": "Món chè tráng miệng thanh mát cuối ngày",
                    "rescue_price": Decimal("15000.00"),
                    "rule_discount_price": Decimal("8400.00"),
                    "pickup_start_time": time(21, 0),
                    "pickup_end_time": time(22, 30),
                    "total_quantity": 10,
                    "remaining_quantity": 5,
                    "allergens": [
                        {
                            "allergen": "Sesame (Mè)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Thành phần mè đen",
                        }
                    ],
                    "dietary_notes": ["Ăn nóng ngon lành", "Vị ngọt thanh"],
                },
            },
        ],
    },
    # --------------------------------------------------------------------------
    # CLUSTER 3: TP. THỦ ĐỨC (Làng Đại Học ĐHQG - Thiên đường Sinh viên KHTN/BK)
    # --------------------------------------------------------------------------
    {
        "merchant_email": "merchant.akhang@ecobite.vn",
        "merchant_name": "Trần Văn Khang",
        "phone": "0904000001",
        "name": "Cơm Tấm Sinh Viên A Khang - KTX Khu B",
        "description": "Quán cơm quen thuộc của hàng vạn sinh viên Làng Đại Học, đĩa cơm đầy ắp gi",
        "address": "Đường Vành Đai ĐHQG, Phường Đông Hòa, TP. Dĩ An / Thủ Đức",
        "location": "POINT(106.8042 10.8785)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
        "rating_avg": Decimal("4.80"),
        "rating_count": 280,
        "total_co2_saved_kg": Decimal("620.00"),
        "menu_items": [
            {
                "name": "Cơm Sườn Trứng Ốp La Sinh Viên",
                "description": "Đĩa cơm tấm thơm nhiều cơm, sườn ướp đậm đà và trứng ốp la lòng đà",
                "category": ItemCategory.RICE,
                "original_price": Decimal("30000.00"),
                "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=600",
                "standard_ingredients": ["Gạo tấm", "Sườn heo", "Trứng gà", "Mỡ hành", "Dưa chua"],
                "base_allergens": ["Eggs (Trứng)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Cơm Sườn Ốp La (Cứu Trợ Sinh Viên Ca Trưa)",
                    "description": "Suất cơm thơm ngon nóng sốt cho sinh viên học ca chiều",
                    "rescue_price": Decimal("16000.00"),
                    "rule_discount_price": Decimal("9000.00"),
                    "pickup_start_time": time(13, 0),
                    "pickup_end_time": time(14, 30),
                    "total_quantity": 20,
                    "remaining_quantity": 12,
                    "allergens": [
                        {
                            "allergen": "Eggs (Trứng)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Có trứng ốp la",
                        }
                    ],
                    "dietary_notes": ["Nhiều cơm", "Canh cải miễn phí"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.omai@ecobite.vn",
        "merchant_name": "Nguyễn Thị Mai",
        "phone": "0904000002",
        "name": "Bún Bò Huế O Mai - Nhà Văn Hóa Sinh Viên",
        "description": "Tô bún bò Huế thơm mùi mắm ruốc nồng nàn, sợi bún to, chả cua giòn ngọt",
        "address": "Quảng trường Sáng Tạo, Làng Đại Học, TP. Thủ Đức, TP. Hồ Chí Minh",
        "location": "POINT(106.8028 10.8752)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=500",
        "rating_avg": Decimal("4.76"),
        "rating_count": 165,
        "total_co2_saved_kg": Decimal("340.00"),
        "menu_items": [
            {
                "name": "Bún Bò Nạm Chả Cua Huế",
                "description": "Nạm bò hầm mềm, chả cua Huế đặc trưng, nước dùng thơm hương sả và",
                "category": ItemCategory.NOODLES,
                "original_price": Decimal("35000.00"),
                "image_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=600",
                "standard_ingredients": [
                    "Bún gạo tươi",
                    "Thịt nạm bò",
                    "Chả cua",
                    "Hành tây",
                    "Rau bắp chuối",
                ],
                "base_allergens": ["Crustaceans (Cua)", "Fish (Mắm ruốc)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Bún Bò Nạm Chả Cua (Ca Chiều)",
                    "description": "Tô bún bò đậm vị Huế nước dùng nóng hổi",
                    "rescue_price": Decimal("20000.00"),
                    "rule_discount_price": Decimal("10500.00"),
                    "pickup_start_time": time(17, 0),
                    "pickup_end_time": time(19, 0),
                    "total_quantity": 12,
                    "remaining_quantity": 7,
                    "allergens": [
                        {
                            "allergen": "Crustaceans (Cua)",
                            "risk_level": "MEDIUM",
                            "source": "INFERRED",
                            "reason": "Chả cua nặn",
                        }
                    ],
                    "dietary_notes": ["Cay vừa", "Nhiều rau bắp chuối"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.maihai@ecobite.vn",
        "merchant_name": "Phan Văn Hải",
        "phone": "0904000003",
        "name": "Bánh Mì Má Hải - Ngã Tư ĐH Quốc Tế",
        "description": "Ổ bánh mì chả cá chiên tại chỗ giòn rụm với nước sốt ớt tỏi trứ danh sinh",
        "address": "Đường Nguyễn Du, Khu phố 6, Linh Trung, TP. Thủ Đức, TP. Hồ Chí Minh",
        "location": "POINT(106.7995 10.8732)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500",
        "rating_avg": Decimal("4.86"),
        "rating_count": 230,
        "total_co2_saved_kg": Decimal("450.00"),
        "menu_items": [
            {
                "name": "Bánh Mì Chả Cá Nóng Giòn",
                "description": "Chả cá sợi ép chiên vàng rộm, dưa leo, rau răm và sốt ớt tỏi bí tr",
                "category": ItemCategory.BAKERY,
                "original_price": Decimal("20000.00"),
                "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600",
                "standard_ingredients": [
                    "Bột mì",
                    "Chả cá basa tươi",
                    "Rau răm",
                    "Dưa leo",
                    "Nước mắm tỏi ớt",
                ],
                "base_allergens": ["Gluten", "Fish (Cá)"],
                "dietary_type": DietaryType.NON_VEGAN,
                "dish": {
                    "name": "Bánh Mì Chả Cá (Ca Chiều Tối)",
                    "description": "Bánh mì giòn rụm thơm lừng chả cá nóng",
                    "rescue_price": Decimal("11000.00"),
                    "rule_discount_price": Decimal("6000.00"),
                    "pickup_start_time": time(18, 0),
                    "pickup_end_time": time(19, 30),
                    "total_quantity": 20,
                    "remaining_quantity": 11,
                    "allergens": [
                        {
                            "allergen": "Fish (Cá)",
                            "risk_level": "HIGH",
                            "source": "EXPLICIT",
                            "reason": "Chả cá biển",
                        }
                    ],
                    "dietary_notes": ["Rau răm thơm", "Vị chua ngọt cay"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.bobapop@ecobite.vn",
        "merchant_name": "Lê Bảo Nam",
        "phone": "0904000004",
        "name": "Trà Sữa Bobapop - Kiot Làng Đại Học",
        "description": "Thương hiệu trà sữa Đài Loan được thế hệ sinh viên ĐHQG đặc biệt yêu thích",
        "address": "Kiot 12 Đường A1, Khu Đô Thị ĐHQG, TP. Thủ Đức, TP. Hồ Chí Minh",
        "location": "POINT(106.8055 10.8803)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1556881286-fc6915169721?w=500",
        "rating_avg": Decimal("4.72"),
        "rating_count": 140,
        "total_co2_saved_kg": Decimal("210.00"),
        "menu_items": [
            {
                "name": "Trà Sữa Trân Châu Bobapop",
                "description": "Trà đen Assam đậm đà, sữa béo ngậy và trân châu đen truyền thống t",
                "category": ItemCategory.BEVERAGE,
                "original_price": Decimal("38000.00"),
                "image_url": "https://images.unsplash.com/photo-1556881286-fc6915169721?w=600",
                "standard_ingredients": [
                    "Cốt trà đen",
                    "Bột sữa",
                    "Trân châu đường đen",
                    "Đường mía",
                ],
                "base_allergens": ["Milk (Sữa)"],
                "dietary_type": DietaryType.VEGETARIAN,
                "dish": {
                    "name": "Trà Sữa Trân Châu (Giải Cứu Ca Tối)",
                    "description": "Ly trà sữa ngọt ngào xua tan căng thẳng sau giờ học",
                    "rescue_price": Decimal("20000.00"),
                    "rule_discount_price": Decimal("11400.00"),
                    "pickup_start_time": time(20, 30),
                    "pickup_end_time": time(22, 0),
                    "total_quantity": 10,
                    "remaining_quantity": 6,
                    "allergens": [
                        {
                            "allergen": "Milk (Sữa)",
                            "risk_level": "MEDIUM",
                            "source": "EXPLICIT",
                            "reason": "Sữa bột nguyên kem",
                        }
                    ],
                    "dietary_notes": ["Độ ngọt 70%", "Trân châu dẻo"],
                },
            },
        ],
    },
    {
        "merchant_email": "merchant.chaykhtn@ecobite.vn",
        "merchant_name": "Võ Văn Tâm",
        "phone": "0904000005",
        "name": "Cơm Chay Bình An - Cổng Sau ĐH KHTN Linh Trung",
        "description": "Cơm chay sinh viên thơm ngon ấm áp bên hông trường Đại học Khoa học Tự nhi",
        "address": "Đường số 8, Phường Linh Trung, TP. Thủ Đức, TP. Hồ Chí Minh",
        "location": "POINT(106.7971 10.8698)",
        "kyc_status": KycStatus.APPROVED,
        "avatar_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
        "rating_avg": Decimal("4.93"),
        "rating_count": 210,
        "total_co2_saved_kg": Decimal("510.00"),
        "menu_items": [
            {
                "name": "Cơm Chay Tự Chọn 4 Món",
                "description": "Đĩa cơm chay gạo huyết rồng ăn kèm nấm kho tiêu, đậu hũ sốt cà, ch",
                "category": ItemCategory.VEGETARIAN,
                "original_price": Decimal("25000.00"),
                "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600",
                "standard_ingredients": [
                    "Gạo lứt",
                    "Nấm đùi gà",
                    "Đậu hũ",
                    "Cà chua",
                    "Rau luộc kho quẹt",
                ],
                "base_allergens": ["Soybeans (Đậu nành)"],
                "dietary_type": DietaryType.VEGAN,
                "dish": {
                    "name": "Cơm Chay Tự Chọn (Ca Trưa Muộn)",
                    "description": "Bữa cơm chay thanh sạch nhẹ bụng giàu dinh dưỡng",
                    "rescue_price": Decimal("13000.00"),
                    "rule_discount_price": Decimal("7500.00"),
                    "pickup_start_time": time(13, 0),
                    "pickup_end_time": time(14, 30),
                    "total_quantity": 15,
                    "remaining_quantity": 9,
                    "allergens": [],
                    "dietary_notes": ["Thuần chay", "Tốt cho tiêu hóa"],
                },
            },
        ],
    },
    # --------------------------------------------------------------------------
    # TEST CASES FOR ADMIN KYC REVIEW WORKFLOW (PENDING & REJECTED)
    # --------------------------------------------------------------------------
    {
        "merchant_email": "merchant.boke@ecobite.vn",
        "merchant_name": "Hoàng Văn Thái",
        "phone": "0905000001",
        "name": "Quán Nướng Bờ Kè Trường Sa (Chờ Duyệt KYC)",
        "description": "Quán nướng bia hơi bình dân mới nộp hồ sơ xin tham gia nền tảng EcoBite",
        "address": "120 Trường Sa, Phường 17, Quận Bình Thạnh, TP. Hồ Chí Minh",
        "location": "POINT(106.7021 10.7915)",
        "kyc_status": KycStatus.PENDING,
        "kyc_license_url": "https://ecobite.vn/static/kyc/license_boke_pending.pdf",
        "avatar_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
        "rating_avg": Decimal("5.00"),
        "rating_count": 0,
        "total_co2_saved_kg": Decimal("0.00"),
        "menu_items": [],
    },
    {
        "merchant_email": "merchant.nuocep@ecobite.vn",
        "merchant_name": "Đỗ Thị Quỳnh",
        "phone": "0905000002",
        "name": "Tiệm Nước Ép Trái Cây Nguyên Chất (Chờ Duyệt KYC)",
        "description": "Chuyên các dòng nước ép trái cây tươi nguyên chất không đường",
        "address": "45 Tô Hiến Thành, Phường 13, Quận 10, TP. Hồ Chí Minh",
        "location": "POINT(106.6665 10.7780)",
        "kyc_status": KycStatus.PENDING,
        "kyc_license_url": "https://ecobite.vn/static/kyc/license_nuocep_pending.pdf",
        "avatar_url": "https://images.unsplash.com/photo-1556881286-fc6915169721?w=500",
        "rating_avg": Decimal("5.00"),
        "rating_count": 0,
        "total_co2_saved_kg": Decimal("0.00"),
        "menu_items": [],
    },
    {
        "merchant_email": "merchant.hemcu@ecobite.vn",
        "merchant_name": "Bùi Văn Sáu",
        "phone": "0905000003",
        "name": "Tiệm Cơm Văn Phòng Hẻm Cũ (Bị Từ Chối KYC)",
        "description": "Cơ sở nộp giấy phép ATVSTP hết hiệu lực, bị quản trị viên từ chối cấp phép",
        "address": "15/4 Cách Mạng Tháng 8, Phường Bến Thành, Quận 1, TP. Hồ Chí Minh",
        "location": "POINT(106.6908 10.7712)",
        "kyc_status": KycStatus.REJECTED,
        "kyc_reject_reason": (
            "Giấy chứng nhận cơ sở đủ điều kiện ATVSTP đã hết hạn hiệu lực từ ngày 15/0 "
            "9/2026. Đề nghị chủ quán bổ sung giấy cấp mới của Ban Quản lý ATTP TP.HCM."
        ),
        "kyc_license_url": "https://ecobite.vn/static/kyc/license_expired.jpg",
        "avatar_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
        "rating_avg": Decimal("5.00"),
        "rating_count": 0,
        "total_co2_saved_kg": Decimal("0.00"),
        "menu_items": [],
    },
]


async def reset_database() -> None:
    """Drop and recreate all tables in development environment."""
    print("⚠️  Dropping all existing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("🌱 Re-creating tables schema...")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database schema freshly initialized.")


async def seed_data() -> None:
    """Seed comprehensive sample records across all platform tables."""
    async with AsyncSessionLocal() as db:
        # Check idempotency
        existing_admin = await db.execute(select(User).where(User.email == "admin@ecobite.vn"))
        if existing_admin.scalar_one_or_none() is not None:
            print(
                "ℹ️  Sample data already exists. Run with '--reset' if you wish to wipe and re-seed."
            )
            return

        print("🚀 Starting EcoBite comprehensive sample data seeding...")
        hashed_pw = hash_password(DEFAULT_PASSWORD)
        now = datetime.now(UTC)

        # ======================================================================
        # 1. USERS & PREFERENCES (Admin, Consumers)
        # ======================================================================
        print(" [1/5] Creating System Users & Profiles...")
        admin = User(
            email="admin@ecobite.vn",
            hashed_password=hashed_pw,
            full_name="Quản Trị Viên EcoBite",
            phone="0901000001",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )

        consumer_1 = User(
            email="consumer.an@ecobite.vn",
            hashed_password=hashed_pw,
            full_name="Nguyễn Văn An",
            phone="0904000004",
            role=UserRole.CONSUMER,
            is_active=True,
            is_verified=True,
            green_points_balance=180,
        )

        consumer_2 = User(
            email="consumer.bich@ecobite.vn",
            hashed_password=hashed_pw,
            full_name="Lê Thị Bích",
            phone="0905000005",
            role=UserRole.CONSUMER,
            is_active=True,
            is_verified=True,
            green_points_balance=90,
        )

        consumer_3 = User(
            email="consumer.huy@ecobite.vn",
            hashed_password=hashed_pw,
            full_name="Phùng Quốc Huy",
            phone="0906000006",
            role=UserRole.CONSUMER,
            is_active=True,
            is_verified=True,
            green_points_balance=350,
        )

        db.add_all([admin, consumer_1, consumer_2, consumer_3])
        await db.flush()

        # Hồ sơ khẩu vị & Dị ứng (Guardrail #7: Bộ lọc SQL cứng)
        pref_an = UserPreference(
            user=consumer_1,
            preferred_categories=["RICE", "NOODLES"],
            dietary_preference=DietaryPreference.NONE,
            excluded_allergens=["Đậu phộng", "Peanuts (Đậu phộng)"],
            max_budget=Decimal("45000.00"),
        )
        pref_bich = UserPreference(
            user=consumer_2,
            preferred_categories=["BAKERY", "VEGETARIAN"],
            dietary_preference=DietaryPreference.VEGETARIAN,
            excluded_allergens=["Hải sản", "Milk (Sữa)"],
            max_budget=Decimal("35000.00"),
        )
        pref_huy = UserPreference(
            user=consumer_3,
            preferred_categories=["RICE", "NOODLES", "BAKERY"],
            dietary_preference=DietaryPreference.NONE,
            excluded_allergens=[],
            max_budget=Decimal("50000.00"),
        )
        db.add_all([pref_an, pref_bich, pref_huy])

        # ======================================================================
        # 2. STORES, MENU ITEMS & SURPLUS DISHES (23 Real Spots across 3 Clusters)
        # ======================================================================
        print(
            f" [2/5] Creating {len(STORE_SEEDS_DATA)} Real Stores across Q1, Q5, and TP. Thủ Đức..."
        )
        seeded_stores: list[Store] = []
        seeded_dishes: list[Dish] = []

        for s_data in STORE_SEEDS_DATA:
            merchant = User(
                email=s_data["merchant_email"],
                hashed_password=hashed_pw,
                full_name=s_data["merchant_name"],
                phone=s_data["phone"],
                role=UserRole.STORE_PARTNER,
                is_active=True,
                is_verified=True,
            )
            db.add(merchant)
            await db.flush()

            store = Store(
                owner=merchant,
                name=s_data["name"],
                description=s_data["description"],
                address=s_data["address"],
                phone=s_data["phone"],
                avatar_url=s_data["avatar_url"],
                kyc_license_url=s_data.get("kyc_license_url"),
                kyc_status=s_data["kyc_status"],
                kyc_reject_reason=s_data.get("kyc_reject_reason"),
                location=s_data["location"],
                rating_avg=s_data["rating_avg"],
                rating_count=s_data["rating_count"],
                total_co2_saved_kg=s_data["total_co2_saved_kg"],
            )
            db.add(store)
            await db.flush()
            seeded_stores.append(store)

            # Tạo Menu Items & Active Dishes
            for m_data in s_data.get("menu_items", []):
                menu_item = MenuItem(
                    store=store,
                    name=m_data["name"],
                    description=m_data["description"],
                    category=m_data["category"],
                    original_price=m_data["original_price"],
                    image_url=m_data["image_url"],
                    standard_ingredients=m_data["standard_ingredients"],
                    base_allergens=m_data["base_allergens"],
                    dietary_type=m_data["dietary_type"],
                    is_active=True,
                )
                db.add(menu_item)
                await db.flush()

                # Nếu có món ăn giải cứu đăng bán
                d_info = m_data.get("dish")
                if d_info:
                    p_end = d_info["pickup_end_time"]
                    dt_rush = datetime.combine(datetime.today().date(), p_end) - timedelta(
                        minutes=45
                    )
                    dish = Dish(
                        store=store,
                        menu_item=menu_item,
                        name=d_info["name"],
                        description=d_info["description"],
                        category=m_data["category"],
                        image_url=m_data["image_url"],
                        original_price=m_data["original_price"],
                        rescue_price=d_info["rescue_price"],
                        rule_discount_price=d_info["rule_discount_price"],
                        pickup_start_time=d_info["pickup_start_time"],
                        pickup_end_time=p_end,
                        rule_discount_start_time=dt_rush.time(),
                        total_quantity=d_info["total_quantity"],
                        remaining_quantity=d_info["remaining_quantity"],
                        status=DishStatus.ACTIVE,
                        ingredients=m_data["standard_ingredients"],
                        allergens=d_info.get("allergens", []),
                        dietary_notes=d_info.get("dietary_notes", []),
                        dietary_type=m_data["dietary_type"],
                        estimated_co2_kg_per_dish=Decimal("2.50"),
                    )
                    db.add(dish)
                    seeded_dishes.append(dish)

        await db.flush()
        print(
            f"       ✅ Successfully seeded {len(seeded_stores)} stores "
            f"and {len(seeded_dishes)} active surplus dishes."
        )

        # ======================================================================
        # 3. VOUCHERS & GAMIFICATION (Green Points)
        # ======================================================================
        print(" [3/5] Creating Vouchers & Green Points Rewards...")
        voucher_1 = Voucher(
            code="ECOBITE10K",
            title="Voucher Giải Cứu Xanh 10.000đ",
            description="Giảm ngay 10.000đ cho đơn món giải cứu từ 30.000đ",
            discount_amount=Decimal("10000.00"),
            points_required=100,
            min_order_amount=Decimal("30000.00"),
            expires_at=now + timedelta(days=60),
            is_active=True,
        )

        voucher_2 = Voucher(
            code="GREENHERO20K",
            title="Đại Sứ Xanh EcoBite 20.000đ",
            description="Giảm 20.000đ cho đơn cứu trợ thực phẩm từ 50.000đ",
            discount_amount=Decimal("20000.00"),
            points_required=180,
            min_order_amount=Decimal("50000.00"),
            expires_at=now + timedelta(days=90),
            is_active=True,
        )

        db.add_all([voucher_1, voucher_2])
        await db.flush()

        # Người dùng An đã đổi 1 voucher
        user_voucher_an = UserVoucher(
            user=consumer_1,
            voucher=voucher_1,
            is_used=False,
            claimed_at=now - timedelta(days=2),
        )
        db.add(user_voucher_an)

        # ======================================================================
        # 4. ORDERS, PAYMENTS, QR TOKENS & REVIEWS
        # ======================================================================
        print(" [4/5] Creating Sample Confirmed Orders & HMAC QR Tokens...")
        if seeded_dishes:
            sample_dish = seeded_dishes[0]
            sample_store = seeded_stores[0]

            order_1 = Order(
                order_code="EB-20261102-0001",
                consumer=consumer_1,
                store=sample_store,
                dish=sample_dish,
                quantity=1,
                unit_price=sample_dish.rescue_price,
                total_amount=sample_dish.rescue_price,
                payment_method=PaymentMethod.VNPAY,
                payment_status=PaymentStatus.PAID,
                status=OrderStatus.CONFIRMED,
                pickup_deadline=datetime.combine(now.date(), sample_dish.pickup_end_time),
                vnpay_pay_date=now - timedelta(minutes=25),
                vnpay_transaction_no="14567890",
                vnpay_bank_code="NCB",
                co2_saved_kg=Decimal("2.50"),
                green_points_earned=50,
            )
            db.add(order_1)
            await db.flush()

            # Dynamic QR Token (HMAC-SHA256 signature)
            qr_token = QRToken(
                order=order_1,
                token_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                nonce="sample-cryptographic-nonce-123456",
                is_used=False,
                expires_at=now + timedelta(hours=2),
            )
            db.add(qr_token)

            # Payment Transaction (VNPay)
            tx = PaymentTransaction(
                order=order_1,
                payment_provider="VNPAY",
                txn_ref=order_1.order_code,
                vnp_transaction_no="14567890",
                vnp_bank_code="NCB",
                vnp_response_code="00",
                amount=sample_dish.rescue_price,
                is_verified=True,
                raw_ipn_payload={"vnp_ResponseCode": "00", "vnp_TxnRef": order_1.order_code},
                created_at=now - timedelta(minutes=25),
            )
            db.add(tx)

            # Review hoàn tất
            review = Review(
                order=order_1,
                consumer=consumer_1,
                dish=sample_dish,
                store=sample_store,
                rating=5,
                comment=(
                    "Cơm tấm rất ngon, sườn dày và còn nóng hổi. "
                    "Rất ủng hộ dự án giải cứu thực phẩm!"
                ),
                tags=["Ngon", "Giá tốt", "Đúng giờ"],
            )
            db.add(review)

            # Green Points Ledger (+50 points)
            points_entry = GreenPointsLedger(
                user=consumer_1,
                order=order_1,
                points_change=50,
                balance_after=230,
                action_type=PointActionType.ORDER_RESCUE,
                co2_saved_kg=Decimal("2.50"),
                note="Cộng 50 Điểm Xanh giải cứu 1 suất Cơm Sườn Bì Chả",
            )
            db.add(points_entry)

        # ======================================================================
        # 5. NOTIFICATIONS
        # ======================================================================
        print(" [5/5] Creating System & Order Notifications...")
        noti_1 = Notification(
            user=consumer_1,
            title="Đơn hàng giải cứu đã xác nhận!",
            message=(
                "Đơn hàng EB-20261102-0001 đã thanh toán thành công. Hãy tới lấy món trước hạn nhé!"
            ),
            type=NotificationType.ORDER_UPDATE,
            metadata_payload={"order_id": str(order_1.id)} if seeded_dishes else {},
            is_read=False,
        )
        db.add(noti_1)

        await db.commit()
        print(
            "🎉 Seeding completed successfully! 23 Stores, Real PostGIS coordinates, "
            "Menus, Dishes, and Users are ready."
        )


async def main() -> None:
    """Entry point for command line execution."""
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        await reset_database()
    await seed_data()


if __name__ == "__main__":
    asyncio.run(main())
