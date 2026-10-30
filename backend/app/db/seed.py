"""Database seeding script for EcoBite Platform.

Provides rich, realistic sample data matching the business specifications in
docs/01_PRD_and_User_Stories.md and docs/03_Database_Schema_ERD.md.

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


async def reset_database() -> None:
    """Drop and recreate all tables in development environment."""
    print("⚠️  Dropping all existing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("🌱 Re-creating tables schema...")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database schema freshly initialized.")


async def seed_data() -> None:
    """Seed comprehensive sample records across all 13 platform tables."""
    async with AsyncSessionLocal() as db:
        # Check idempotency
        existing_admin = await db.execute(select(User).where(User.email == "admin@ecobite.vn"))
        if existing_admin.scalar_one_or_none() is not None:
            print(
                "ℹ️  Sample data already exists. Run with '--reset' if you wish to wipe and re-seed."
            )
            return

        print("🚀 Starting EcoBite sample data seeding...")
        hashed_pw = hash_password(DEFAULT_PASSWORD)
        now = datetime.now(UTC)

        # ======================================================================
        # 1. USERS & PREFERENCES (Cụm 1)
        # ======================================================================
        print(" [1/5] Creating Users & Profiles...")
        admin = User(
            email="admin@ecobite.vn",
            hashed_password=hashed_pw,
            full_name="Quản Trị Viên EcoBite",
            phone="0901000001",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )

        merchant_1 = User(
            email="merchant.comtam@ecobite.vn",
            hashed_password=hashed_pw,
            full_name="Nguyễn Văn Hùng",
            phone="0902000002",
            role=UserRole.STORE_PARTNER,
            is_active=True,
            is_verified=True,
        )

        merchant_2 = User(
            email="merchant.bakery@ecobite.vn",
            hashed_password=hashed_pw,
            full_name="Trần Thị Lan",
            phone="0903000003",
            role=UserRole.STORE_PARTNER,
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

        db.add_all([admin, merchant_1, merchant_2, consumer_1, consumer_2])
        await db.flush()

        # Hồ sơ khẩu vị & Dị ứng (Guardrail #7: Bộ lọc SQL cứng)
        pref_an = UserPreference(
            user=consumer_1,
            preferred_categories=["RICE", "NOODLES"],
            dietary_preference=DietaryPreference.NONE,
            excluded_allergens=["Đậu phộng"],  # Dị ứng lạc/đậu phộng
            max_budget=Decimal("45000.00"),
        )
        pref_bich = UserPreference(
            user=consumer_2,
            preferred_categories=["BAKERY", "VEGETARIAN"],
            dietary_preference=DietaryPreference.VEGETARIAN,
            excluded_allergens=["Hải sản", "Sữa"],
            max_budget=Decimal("35000.00"),
        )
        db.add_all([pref_an, pref_bich])

        # ======================================================================
        # 2. STORES (Cụm 1)
        # ======================================================================
        print(" [2/5] Creating Stores & KYC records...")
        store_1 = Store(
            owner=merchant_1,
            name="Cơm Tấm Sài Gòn Đêm 1982",
            description="Chuyên các món cơm tấm sườn bì chả than hoa truyền thống Sài Gòn",
            address="135 Hai Bà Trưng, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            phone="02838221982",
            avatar_url="https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
            kyc_license_url="https://ecobite.vn/static/kyc/license_comtam.jpg",
            kyc_status=KycStatus.APPROVED,
            location="POINT(106.6974 10.7788)",
            rating_avg=Decimal("4.85"),
            rating_count=142,
            total_co2_saved_kg=Decimal("355.00"),
        )

        store_2 = Store(
            owner=merchant_2,
            name="Tiệm Bánh Mì Artisan Sài Gòn",
            description="Bánh mì thủ công lên men tự nhiên, bánh ngọt tươi nướng mới mỗi ngày",
            address="42 Trần Hưng Đạo, Phường Phạm Ngũ Lão, Quận 1, TP. Hồ Chí Minh",
            phone="02838364242",
            avatar_url="https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500",
            kyc_license_url="https://ecobite.vn/static/kyc/license_bakery.jpg",
            kyc_status=KycStatus.APPROVED,
            location="POINT(106.6923 10.7681)",
            rating_avg=Decimal("4.92"),
            rating_count=88,
            total_co2_saved_kg=Decimal("220.00"),
        )

        db.add_all([store_1, store_2])
        await db.flush()

        # ======================================================================
        # 3. MENU ITEMS & DISHES (Cụm 2 - Menu Grounding & Food Rescue)
        # ======================================================================
        print(" [3/5] Creating Menu Items & Active Rescue Dishes...")
        # Menu chuẩn của quán (Menu Grounding)
        item_com_suon = MenuItem(
            store=store_1,
            name="Cơm Sườn Bì Chả Nướng Than Hoa",
            description="Sườn cốt lết ướp mật ong nướng than, chả trứng hấp, bì heo trộn thính",
            category=ItemCategory.RICE,
            original_price=Decimal("55000.00"),
            image_url="https://images.unsplash.com/photo-1544025162-d76694265947?w=600",
            standard_ingredients=["Gạo tấm", "Sườn heo", "Bì heo", "Trứng", "Mỡ hành"],
            base_allergens=["Trứng"],
            dietary_type=DietaryType.NON_VEGAN,
            is_active=True,
        )

        item_com_ga = MenuItem(
            store=store_1,
            name="Cơm Đùi Gà Nướng Sốt Teriyaki",
            description="Đùi gà góc tư nướng mềm ngọt ăn kèm dưa chua",
            category=ItemCategory.RICE,
            original_price=Decimal("50000.00"),
            image_url="https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=600",
            standard_ingredients=["Gạo tấm", "Thịt gà", "Nước tương", "Mè rang"],
            base_allergens=["Mè", "Gluten"],
            dietary_type=DietaryType.NON_VEGAN,
            is_active=True,
        )

        item_banh_mi = MenuItem(
            store=store_2,
            name="Bánh Mì Thịt Nướng Đặc Biệt",
            description="Bánh mì vỏ giòn ruột xốp kẹp thịt nướng xiên que, đồ chua, ngò rí",
            category=ItemCategory.BAKERY,
            original_price=Decimal("35000.00"),
            image_url="https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600",
            standard_ingredients=["Bột mì", "Thịt heo nướng", "Dưa leo", "Đồ chua", "Nước sốt"],
            base_allergens=["Gluten"],
            dietary_type=DietaryType.NON_VEGAN,
            is_active=True,
        )

        item_croissant = MenuItem(
            store=store_2,
            name="Bánh Croissant Bơ Pháp Thượng Hạng",
            description="Bánh sừng bò nướng ngậy bơ thơm phức nhiều lớp giòn xốp",
            category=ItemCategory.BAKERY,
            original_price=Decimal("40000.00"),
            image_url="https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=600",
            standard_ingredients=["Bột mì", "Bơ lạt Pháp", "Sữa tươi", "Men"],
            base_allergens=["Gluten", "Sữa"],
            dietary_type=DietaryType.VEGETARIAN,
            is_active=True,
        )

        db.add_all([item_com_suon, item_com_ga, item_banh_mi, item_croissant])
        await db.flush()

        # Món ăn dư thừa đăng bán trong ca giải cứu (Rescue Dishes)
        dish_com_suon = Dish(
            store=store_1,
            menu_item=item_com_suon,
            name="Cơm Sườn Bì Chả Nướng (Ca Trưa Muộn)",
            description="Suất cơm trưa còn dư chất lượng tuyệt đối, đóng hộp giữ nóng",
            category=ItemCategory.RICE,
            original_price=Decimal("55000.00"),
            rescue_price=Decimal("30000.00"),  # Giảm ~45%
            rule_discount_price=Decimal("16500.00"),  # Giảm 70% giờ chót
            pickup_start_time=time(13, 30),
            pickup_end_time=time(15, 30),
            rule_discount_start_time=time(14, 45),
            total_quantity=10,
            remaining_quantity=6,
            status=DishStatus.ACTIVE,
            image_url=item_com_suon.image_url,
            ingredients=["Gạo tấm", "Sườn heo nướng", "Chả trứng", "Bì heo", "Mỡ hành"],
            # Cảnh báo dị ứng 2 tầng (Guardrail #6)
            allergens=[
                {
                    "allergen": "Trứng",
                    "risk_level": "MEDIUM",
                    "source": "EXPLICIT",
                    "reason": "Chủ quán xác nhận có chả trứng",
                }
            ],
            dietary_notes=["Có mỡ hành", "Kèm dưa chua và nước mắm ớt"],
            dietary_type=DietaryType.NON_VEGAN,
            estimated_co2_kg_per_dish=Decimal("2.50"),
        )

        dish_banh_mi = Dish(
            store=store_2,
            menu_item=item_banh_mi,
            name="Bánh Mì Thịt Nướng (Ca Chiều Tan Tầm)",
            description="Mẻ bánh mì mới ra lò cuối ngày, giòn tan kèm thịt nướng nóng",
            category=ItemCategory.BAKERY,
            original_price=Decimal("35000.00"),
            rescue_price=Decimal("18000.00"),  # Giảm ~48%
            rule_discount_price=Decimal("10500.00"),  # Giảm 70%
            pickup_start_time=time(17, 30),
            pickup_end_time=time(19, 30),
            rule_discount_start_time=time(18, 45),
            total_quantity=15,
            remaining_quantity=11,
            status=DishStatus.ACTIVE,
            image_url=item_banh_mi.image_url,
            ingredients=["Bột mì", "Thịt heo nướng", "Dưa leo", "Đồ chua"],
            allergens=[
                {
                    "allergen": "Gluten",
                    "risk_level": "HIGH",
                    "source": "INFERRED",
                    "reason": "AI suy luận vỏ bánh mì chứa bột lúa mì",
                }
            ],
            dietary_notes=["Ít cay", "Nhiều ngò rí"],
            dietary_type=DietaryType.NON_VEGAN,
            estimated_co2_kg_per_dish=Decimal("1.80"),
        )

        db.add_all([dish_com_suon, dish_banh_mi])
        await db.flush()

        # ======================================================================
        # 4. VOUCHERS & GAMIFICATION (Cụm 4)
        # ======================================================================
        print(" [4/5] Creating Vouchers & Green Points Ledger...")
        voucher_1 = Voucher(
            code="ECOBITE10K",
            title="Voucher Xanh 10.000đ",
            description="Giảm 10.000đ cho đơn cứu trợ từ 30.000đ",
            discount_amount=Decimal("10000.00"),
            points_required=100,
            min_order_amount=Decimal("30000.00"),
            expires_at=now + timedelta(days=60),
            is_active=True,
        )

        voucher_2 = Voucher(
            code="GREENHERO20K",
            title="Đại Sứ Xanh 20.000đ",
            description="Giảm 20.000đ cho đơn cứu trợ từ 50.000đ",
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
        # 5. ORDERS, QR TOKENS, PAYMENTS, REVIEWS & NOTIFICATIONS (Cụm 3 & 5)
        # ======================================================================
        print(" [5/5] Creating Sample Order, QR Token, Payment & Review...")
        # Đơn hàng mẫu đã hoàn thành
        order_sample = Order(
            order_code="EB-20261028-9801",
            consumer=consumer_1,
            store=store_1,
            dish=dish_com_suon,
            quantity=1,
            unit_price=dish_com_suon.rescue_price,
            total_amount=dish_com_suon.rescue_price,
            status=OrderStatus.COMPLETED,
            payment_method=PaymentMethod.VNPAY,
            payment_status=PaymentStatus.PAID,
            vnpay_transaction_no="14072230",
            vnpay_bank_code="NCB",
            vnpay_pay_date=now - timedelta(days=1),
            co2_saved_kg=Decimal("2.50"),
            green_points_earned=25,
            pickup_deadline=now - timedelta(days=1, hours=2),
            completed_at=now - timedelta(days=1, hours=1),
            created_at=now - timedelta(days=1, hours=3),
        )
        db.add(order_sample)
        await db.flush()

        # QR Token đã được quét nhận món (Guardrail #3)
        qr_token_sample = QRToken(
            order=order_sample,
            token_hash="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
            nonce="ecobite_nonce_9901_seed",
            expires_at=order_sample.pickup_deadline,
            is_used=True,
            used_at=order_sample.completed_at,
            created_at=order_sample.created_at,
        )
        db.add(qr_token_sample)

        # Giao dịch thanh toán VNPay IPN (Guardrail #3)
        payment_sample = PaymentTransaction(
            order=order_sample,
            payment_provider="VNPAY",
            txn_ref=order_sample.order_code,
            amount=order_sample.total_amount,
            vnp_transaction_no="14072230",
            vnp_bank_code="NCB",
            vnp_response_code="00",
            is_verified=True,
            raw_ipn_payload={
                "vnp_Amount": "3000000",
                "vnp_BankCode": "NCB",
                "vnp_ResponseCode": "00",
                "vnp_TransactionNo": "14072230",
                "vnp_TxnRef": order_sample.order_code,
            },
            created_at=order_sample.created_at,
        )
        db.add(payment_sample)

        # Đánh giá đơn hàng (Review 1-1 với Order)
        review_sample = Review(
            order=order_sample,
            consumer=consumer_1,
            store=store_1,
            dish=dish_com_suon,
            rating=5,
            comment="Cơm sườn vẫn còn ấm, bì chả rất thơm! Ủng hộ quán giải cứu món ăn.",
            tags=["Ngon", "Nóng hổi", "Đóng gói kỹ"],
            photo_urls=["https://images.unsplash.com/photo-1544025162-d76694265947?w=500"],
            created_at=now - timedelta(days=1, minutes=30),
        )
        db.add(review_sample)

        # Ghi nhận sổ cái Điểm Xanh
        ledger_sample = GreenPointsLedger(
            user=consumer_1,
            order=order_sample,
            points_change=25,
            balance_after=180,
            action_type=PointActionType.ORDER_RESCUE,
            co2_saved_kg=Decimal("2.50"),
            note="Cộng 25 Điểm Xanh từ đơn cứu trợ EB-20261028-9801",
            created_at=order_sample.completed_at or now,
        )
        db.add(ledger_sample)

        # Thông báo đẩy
        notif_1 = Notification(
            user=consumer_1,
            title="Đơn hàng giải cứu hoàn tất 🎉",
            message=(
                f"Bạn đã giải cứu thành công đơn hàng {order_sample.order_code} "
                "và giảm phát thải 2.5 kg CO2!"
            ),
            type=NotificationType.ORDER_UPDATE,
            metadata_payload={
                "order_id": str(order_sample.id),
                "order_code": order_sample.order_code,
            },
            is_read=True,
            created_at=order_sample.completed_at or now,
        )

        notif_2 = Notification(
            user=consumer_1,
            title="Deal giờ chót gần bạn (-70%) 🔥",
            message="Tiệm Bánh Mì Artisan vừa kích hoạt giờ chót giảm 70% chỉ cách bạn 500m!",
            type=NotificationType.NEARBY_DEAL,
            metadata_payload={"store_id": str(store_2.id), "dish_id": str(dish_banh_mi.id)},
            is_read=False,
            created_at=now - timedelta(hours=1),
        )

        db.add_all([notif_1, notif_2])

        await db.commit()
        print("🎉 Seeding completed successfully!")
        print("\n📋 DANH SÁCH TÀI KHOẢN MẪU ĐỂ ĐĂNG NHẬP THỬ NGHIỆM:")
        print(f" • ADMIN:     admin@ecobite.vn           / {DEFAULT_PASSWORD}")
        print(f" • MERCHANT:  merchant.comtam@ecobite.vn / {DEFAULT_PASSWORD}")
        print(f" • MERCHANT:  merchant.bakery@ecobite.vn / {DEFAULT_PASSWORD}")
        print(f" • CONSUMER:  consumer.an@ecobite.vn     / {DEFAULT_PASSWORD}")
        print(f" • CONSUMER:  consumer.bich@ecobite.vn   / {DEFAULT_PASSWORD}")


async def main() -> None:
    reset = "--reset" in sys.argv
    if reset:
        await reset_database()
    await seed_data()


if __name__ == "__main__":
    asyncio.run(main())
