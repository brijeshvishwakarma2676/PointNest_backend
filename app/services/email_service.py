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
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": settings.EMAIL_SERVICE_API_KEY
    }
    
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
