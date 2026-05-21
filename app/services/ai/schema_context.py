# Database table schemas and relation metadata for multi-tenant LLM reasoning.

SCHEMA_CONTEXT = """
Database Type: MySQL / TiDB (Use standard MySQL syntax for dates, limits, aggregations, etc.)

TABLES SCHEMA:

1. `users` (represents Merchants / Shops)
   - id (INT, Primary Key)
   - shop_name (VARCHAR)
   - owner_name (VARCHAR)
   - email (VARCHAR, Unique)
   - phone (VARCHAR)
   - password (VARCHAR)
   - is_active (INT)
   - created_at (DATETIME)
   - updated_at (DATETIME)

2. `customers` (loyalty members of a specific shop)
   - id (INT, Primary Key)
   - shop_id (INT, Foreign Key referencing users.id)
   - name (VARCHAR)
   - phone (VARCHAR, Unique)
   - email (VARCHAR, Unique, Nullable)
   - points (INT, Default 0) - Active loyalty balance
   - is_active (INT, Default 1)
   - created_at (DATETIME)
   - updated_at (DATETIME)
   *Security Note*: All queries involving customers MUST filter by `customers.shop_id = :shop_id`.

3. `purchases` (sales transactions)
   - id (INT, Primary Key)
   - shop_id (INT, Foreign Key referencing users.id)
   - customer_id (INT, Foreign Key referencing customers.id)
   - amount (INT) - Gross transaction amount (before discounts)
   - payable_amount (INT) - Net paid amount (after discounts)
   - points_earned (INT) - Points rewarded for this purchase
   - points_redeemed (INT) - Points redeemed to get discounts in this transaction
   - points_discount (INT) - Discount amount in INR from points (10 points = 1 INR discount)
   - coupon_code (VARCHAR, Nullable) - Voucher code used in this transaction
   - coupon_discount (INT, Default 0) - Discount amount in INR from coupon
   - is_active (INT, Default 1)
   - created_at (DATETIME)
   - updated_at (DATETIME)
   *Security Note*: All queries involving purchases MUST filter by `purchases.shop_id = :shop_id`.

4. `points_ledger` (audit trail of all point earnings and redemptions)
   - id (INT, Primary Key)
   - shop_id (INT, Foreign Key referencing users.id)
   - customer_id (INT, Foreign Key referencing customers.id)
   - type (VARCHAR) - "earn" or "redeem"
   - points (INT) - Points magnitude (positive for earn, negative for redeem)
   - reference_id (INT, Nullable) - purchase_id or redemption_id
   - is_active (INT, Default 1)
   - created_at (DATETIME)
   - updated_at (DATETIME)
   *Security Note*: All queries involving points_ledger MUST filter by `points_ledger.shop_id = :shop_id`.

5. `redemptions` (direct point redemption logs)
   - id (INT, Primary Key)
   - shop_id (INT, Foreign Key referencing users.id)
   - customer_id (INT, Foreign Key referencing customers.id)
   - points_used (INT)
   - amount_discounted (INT) - Discount in INR
   - is_active (INT, Default 1)
   - created_at (DATETIME)
   - updated_at (DATETIME)
   *Security Note*: All queries involving redemptions MUST filter by `redemptions.shop_id = :shop_id`.

6. `coupons` (promotional coupon rules defined by the shop)
   - id (INT, Primary Key)
   - shop_id (INT, Foreign Key referencing users.id)
   - code (VARCHAR, Unique)
   - type (VARCHAR) - "percentage" or "fixed"
   - value (FLOAT)
   - max_discount_cap (FLOAT, Nullable) - Max discount allowed in single transaction
   - min_order_value (FLOAT) - Min order amount required to use this coupon
   - start_date (DATETIME, Nullable)
   - expiry_date (DATETIME, Nullable)
   - max_usage_global (INT)
   - max_usage_per_user (INT)
   - usage_count (INT) - Times used
   - is_stackable (BOOLEAN) - Whether combined with points is allowed
   - eligibility_type (VARCHAR) - "all", "vip", "new", "inactive"
   - status (VARCHAR) - "active", "blocked", "expired"
   - is_active (INT, Default 1)
   - created_at (DATETIME)
   - updated_at (DATETIME)
   *Security Note*: All queries involving coupons MUST filter by `coupons.shop_id = :shop_id`.

7. `coupon_usages` (audit log of coupon redemptions per customer)
   - id (INT, Primary Key)
   - coupon_id (INT, Foreign Key referencing coupons.id)
   - customer_id (INT, Foreign Key referencing customers.id)
   - discount_amount (FLOAT) - Amount saved in INR
   - redeemed_at (DATETIME)
   - is_active (INT, Default 1)
   - created_at (DATETIME)
   - updated_at (DATETIME)
   *Security Note*: All queries involving coupon_usages MUST filter by `coupon_usages.customer_id IN (SELECT id FROM customers WHERE shop_id = :shop_id)`.

8. `notifications` (system, financial, security or audit notifications for a specific shop)
   - id (INT, Primary Key)
   - shop_id (INT, Foreign Key referencing users.id)
   - title (VARCHAR)
   - body (TEXT)
   - type (VARCHAR) - "system", "financial", "security", or "audit"
   - is_read (BOOLEAN)
   - created_at (DATETIME)
   *Security Note*: All queries involving notifications MUST filter by `notifications.shop_id = :shop_id`.
"""
