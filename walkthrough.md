# Final Walkthrough: Full Coupon & Purchase Integration

I have successfully finished the second stage of the coupon system. You can now use coupons directly while recording a new purchase for a customer.

## Key Features Added

### 1. Unified Purchase Flow
- **Automatic Math**: When you apply a coupon code in the "Add Purchase" page, the system automatically calculates the discount.
- **Fair Points**: Even if a customer uses a 50% off coupon, they still earn the full points based on the original bill amount.
- **Detailed Audit**: The final confirmation screen now shows a clear breakdown:
    - **Subtotal**: The original price.
    - **Discount**: The savings from the coupon.
    - **Net Payable**: The final amount the customer actually pays.
    - **Yield Points**: The points earned (based on Subtotal).

### 2. Backend Integrity
- **One Transaction**: Redeeming a coupon and recording a purchase now happens together as one reliable step.
- **Database Tracking**: Every purchase now saves which coupon was used and how much discount was given.

## How to use the new features:
1. Go to **Record Purchase**.
2. Enter the customer's phone and the total bill amount.
3. Type the coupon code in the new **Voucher Protocol** box and click **Apply**.
4. Click **Authorize Transaction**.
5. Check the breakdown in the popup and click **Confirm & Broadcast**.

> [!TIP]
> You can still use the dedicated **Redeem Coupon** page for simple coupon redemptions that are not tied to a specific point-earning purchase.
