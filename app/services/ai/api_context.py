# API router catalog and route paths for LLM UI-navigation recommendations.

API_CONTEXT = """
FASTAPI ROUTE ENDPOINTS AVAILABLE (Use these paths if recommending API actions):

1. Customers Panel:
   - GET /api/v1/customers/get-details?phone=... or ?customer_id=... -> Get details of a customer.
   - POST /api/v1/customers/find-or-create -> Fetch or enroll new customer.
   - POST /api/v1/customers/list -> Search query & retrieve list of customers.
   - GET /api/v1/customers/ledger?customer_id=... -> Fetch customer points history.

2. Purchases Panel:
   - POST /api/v1/purchases -> Record a purchase transaction (awards points, applies coupons, redeems points).
   - GET /api/v1/purchases -> Get purchase list for the shop.

3. Redemptions Panel:
   - POST /api/v1/redemptions/redeem -> Directly redeem loyalty points.
   - GET /api/v1/redemptions -> Get redemptions log.

4. Coupons Panel:
   - POST /api/v1/coupons -> Create a new promotional voucher.
   - GET /api/v1/coupons -> List all coupons.
   - GET /api/v1/coupons/validate?code=... -> Validate a voucher.
"""
