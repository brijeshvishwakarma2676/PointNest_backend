# Implementation Plan: Stacking Points & Coupons (FK Enhanced)

This plan integrates point redemption into the purchase flow, using foreign keys to link specific redemption and coupon usage records for a perfect audit trail.

## Proposed Changes

### [Backend]
#### [MODIFY] [models/purchase.py](file:///home/openspace/My/Projects/customer_loyalty_portal/app/models/purchase.py)
- **New Columns (Foreign Keys)**:
    - `coupon_usage_id`: Integer (FK to `coupon_usages.id`, Optional)
    - `redemption_id`: Integer (FK to `redemptions.id`, Optional)
- **New Columns (Metrics)**:
    - `points_redeemed`: Integer (Optional) - Total points used.
    - `coupon_discount`: Float (Optional) - Savings from coupon.
    - `points_discount`: Float (Optional) - Savings from points.

#### [MODIFY] [schemas/purchase.py](file:///home/openspace/My/Projects/customer_loyalty_portal/app/schemas/purchase.py)
- Update `PurchaseCreate` to include `points_to_redeem: int = 0`.
- Update `PurchaseResponse` to reflect the linked record IDs and discount breakdown.

#### [MODIFY] [endpoints/purchases.py](file:///home/openspace/My/Projects/customer_loyalty_portal/app/api/v1/endpoints/purchases.py)
- **Refined Atomic Logic**:
    1. Validate Coupon (check `is_stackable`).
    2. Validate Customer Points.
    3. Calculate total Discounts.
    4. Create `Purchase` record.
    5. Create `CouponUsage` record (linked to Purchase).
    6. Create `Redemption` record (linked to Customer, affects Points).
    7. **Final Update**: Link the `Purchase` record back to the `coupon_usage_id` and `redemption_id`.
    8. `db.commit()` only if all steps succeed.

---

### [Frontend]
#### [MODIFY] [AddPurchase.jsx](file:///home/openspace/My/Projects/customer_loyalty_portal_frontend/src/features/purchases/pages/AddPurchase.jsx)
- **Point Balance Display**: Show real-time balance after phone verification.
- **Points Input**: A numeric field for "Points to Redeem".
- **Dynamic Limits**: Set `max` of points input to the lower of (Customer Balance) or (Points needed for ₹0 total).
- **Validation**: Prevent stacking if the coupon is not stackable.
- **Enhanced Confirmation Audit**: Detailed subtotal, coupon, and points breakdown.

## Verification Plan

### Automated Tests
- Test API stacking: Verify `points_discount + coupon_discount + payable_amount = gross_amount`.
- Verify Foreign Keys: Ensure `Purchase.redemption_id` actually points to a valid record in the `redemptions` table.

### Manual Verification
- Test stacking/non-stacking UI toggles.
- Verify point deduction is accurate in the Customer ledger after purchase.
