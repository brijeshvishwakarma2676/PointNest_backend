import logging
import httpx
from typing import Dict, Any, List
from fastapi import BackgroundTasks
from datetime import datetime
import pytz

from app.config.settings import settings

logger = logging.getLogger(__name__)

async def _dispatch_email_api(payload: Dict[str, Any]):
    """
    Direct asynchronous API call to the Vercel email microservice.
    Redirects to svish5633@gmail.com if settings.IS_PROD is False.
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": settings.EMAIL_SERVICE_API_KEY
    }
    
    # Intercept and redirect recipient email if not in production mode
    recipient = payload.get("to_email")
    if not settings.IS_PROD:
        logger.info(f"[DEV MODE] Intersecting outbound email to '{recipient}'. Redirecting to 'svish5633@gmail.com'.")
        payload["to_email"] = "svish5633@gmail.com"
        # Append target recipient to subject line for clean testing
        original_subject = payload.get("subject", "")
        payload["subject"] = f"[DEV REDIRECT] {original_subject} (To: {recipient})"
        
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(f"Dispatching outbound email to: {payload.get('to_email')} via Vercel service...")
            response = await client.post(
                settings.EMAIL_SERVICE_URL,

                json=payload,
                headers=headers
            )
            if response.status_code == 200:
                logger.info(f"Email successfully dispatched: {response.json()}")
            else:
                logger.error(f"Email service returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Failed to communicate with Vercel email service: {str(e)}")

def send_welcome_email(
    background_tasks: BackgroundTasks,
    recipient_email: str,
    customer_name: str,
    initial_points: int = 0
):
    """
    Send a beautiful welcome email to the newly registered customer.
    """
    if not recipient_email:
        return
        
    payload = {
        "to_email": recipient_email,
        "subject": f"Welcome to our Loyalty Program, {customer_name}!",
        "template_name": "index.html",
        "template_context": {
            "title": "Welcome Protocol",
            "heading": f"Welcome, {customer_name}!",
            "body": f"We are thrilled to have you as part of our exclusive loyalty network! You have been successfully registered, and your active balance is <strong>{initial_points} points</strong>. Earn 1 point for every ₹10 spent on future transactions!",
            "action_button_text": "View Dashboard",
            "action_button_url": "https://pointnest-loyalty.vercel.app"
        },
        "sender_name": settings.APP_NAME
    }
    
    # Run email delivery in background to ensure zero lag in API response time!
    background_tasks.add_task(_dispatch_email_api, payload)

def send_purchase_receipt_email(
    background_tasks: BackgroundTasks,
    recipient_email: str,
    customer_name: str,
    amount: int,
    points_earned: int,
    points_redeemed: int,
    points_balance: int,
    savings: int = 0,
    shop_name: str = "PointNest Shop",
    transaction_id: str = "PN-TXN-000000"
):
    """
    Send a transaction confirmation receipt in PointNest branded layout.
    """
    if not recipient_email:
        return
        
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(ist)
    formatted_date = now_ist.strftime("%d/%m/%Y %I:%M %p")
    
    payload = {
        "to_email": recipient_email,
        "subject": f"Payment of INR {amount:.2f} successful at {shop_name} | PointNest",
        "template_name": "receipt.html",
        "template_context": {
            "customer_name": customer_name,
            "amount": float(amount),
            "shop_name": shop_name,
            "transaction_id": transaction_id,
            "date": formatted_date,
            "points_earned": points_earned,
            "points_redeemed": points_redeemed,
            "savings": float(savings),
            "points_balance": points_balance
        },
        "sender_name": settings.APP_NAME
    }
    
    # Run email delivery in background
    background_tasks.add_task(_dispatch_email_api, payload)


def send_otp_email(
    background_tasks: BackgroundTasks,
    recipient_email: str,
    otp_code: str,
    owner_name: str
):
    """
    Send a secure OTP validation email for password recovery.
    """
    if not recipient_email:
        return
        
    payload = {
        "to_email": recipient_email,
        "subject": f"Security Verification Code: {otp_code} | PointNest Recovery",
        "template_name": "index.html",
        "template_context": {
            "title": "Security Authorization Key Reset",
            "heading": "Verification Required",
            "body": f"Dear {owner_name},<br><br>We received a request to authorize a password reset for your PointNest partner terminal profile.<br><br>Your recovery OTP (One-Time Password) is:<br><br><span style='font-size: 32px; font-weight: 800; letter-spacing: 5px; color: #0a0a0b; display: block; margin: 20px 0; text-align: center;'>{otp_code}</span><br>This OTP is valid for 10 minutes. If you did not initiate this recovery protocol, please secure your profile immediately.",
            "action_button_text": "Secure My Terminal",
            "action_button_url": "https://pointnest.com/support"
        },
        "sender_name": settings.APP_NAME
    }
    
    background_tasks.add_task(_dispatch_email_api, payload)

