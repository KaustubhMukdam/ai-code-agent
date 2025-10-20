"""
Stripe payment processing service
"""
import stripe
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from src.api.models import User, BillingTransaction, get_db

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_your_test_key_here")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_your_test_key_here")

# Subscription tier configurations
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free Tier",
        "price": 0,
        "monthly_jobs": 5,
        "languages": ["python"],
        "priority": "standard",
        "stripe_price_id": None
    },
    "pro": {
        "name": "Pro Plan",
        "price": 9.99,
        "monthly_jobs": 50,
        "languages": ["python", "cpp", "java", "javascript"],
        "priority": "high",
        "stripe_price_id": "price_pro_monthly_999"  # Replace with your actual Stripe price ID
    },
    "enterprise": {
        "name": "Enterprise Plan", 
        "price": 29.99,
        "monthly_jobs": 999,
        "languages": ["python", "cpp", "java", "javascript", "go", "rust"],
        "priority": "premium",
        "stripe_price_id": "price_enterprise_monthly_2999"  # Replace with your actual Stripe price ID
    }
}

class StripeService:
    """Handle all Stripe payment operations"""
    
    @staticmethod
    def create_checkout_session(user_id: int, plan_key: str, success_url: str, cancel_url: str) -> Dict:
        """Create a Stripe checkout session for subscription"""
        try:
            plan = SUBSCRIPTION_PLANS.get(plan_key)
            if not plan or not plan["stripe_price_id"]:
                raise ValueError("Invalid subscription plan")
            
            session = stripe.checkout.Session.create(
                customer_email=None,  # Will be filled by user
                line_items=[{
                    'price': plan["stripe_price_id"],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user_id),
                    'plan': plan_key
                },
                allow_promotion_codes=True,
                subscription_data={
                    'trial_period_days': 7  # 7-day free trial
                }
            )
            
            return {
                "checkout_url": session.url,
                "session_id": session.id
            }
            
        except Exception as e:
            print(f"Stripe checkout error: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def create_customer_portal_session(customer_id: str, return_url: str) -> Dict:
        """Create customer portal session for managing subscriptions"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return {"portal_url": session.url}
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def handle_webhook(payload: str, sig_header: str) -> Dict:
        """Handle Stripe webhook events"""
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret")
        
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            return {"error": "Invalid payload"}
        except stripe.error.SignatureVerificationError as e:
            return {"error": "Invalid signature"}
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            StripeService._handle_successful_payment(session)
            
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            StripeService._handle_subscription_payment(invoice)
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            StripeService._handle_subscription_canceled(subscription)
        
        return {"status": "success"}
    
    @staticmethod
    def _handle_successful_payment(session):
        """Handle successful checkout session"""
        user_id = int(session['metadata']['user_id'])
        plan_key = session['metadata']['plan']
        
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            # Update user subscription
            user.subscription_tier = plan_key
            user.subscription_start_date = datetime.utcnow()
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            user.stripe_customer_id = session.get('customer')
            user.stripe_subscription_id = session.get('subscription')
            
            # Reset monthly usage
            user.total_jobs_this_month = 0
            user.monthly_job_limit = SUBSCRIPTION_PLANS[plan_key]["monthly_jobs"]
            
            # Record transaction
            transaction = BillingTransaction(
                user_id=user_id,
                amount=SUBSCRIPTION_PLANS[plan_key]["price"],
                transaction_type="subscription",
                stripe_payment_intent_id=session.get('payment_intent'),
                status="completed"
            )
            
            db.add(transaction)
            db.commit()
            
            print(f"✅ User {user_id} upgraded to {plan_key} plan")
        
        db.close()
    
    @staticmethod
    def _handle_subscription_payment(invoice):
        """Handle recurring subscription payment"""
        customer_id = invoice['customer']
        
        db = next(get_db())
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        
        if user:
            # Extend subscription
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            user.total_jobs_this_month = 0  # Reset monthly usage
            
            # Record transaction
            transaction = BillingTransaction(
                user_id=user.id,
                amount=invoice['amount_paid'] / 100,  # Convert from cents
                transaction_type="subscription_renewal",
                stripe_payment_intent_id=invoice['payment_intent'],
                status="completed"
            )
            
            db.add(transaction)
            db.commit()
            
            print(f"✅ Subscription renewed for user {user.id}")
        
        db.close()
    
    @staticmethod
    def _handle_subscription_canceled(subscription):
        """Handle subscription cancellation"""
        customer_id = subscription['customer']
        
        db = next(get_db())
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        
        if user:
            # Downgrade to free tier
            user.subscription_tier = "free"
            user.monthly_job_limit = SUBSCRIPTION_PLANS["free"]["monthly_jobs"]
            user.stripe_subscription_id = None
            
            db.commit()
            print(f"🔄 User {user.id} downgraded to free tier")
        
        db.close()

# Helper functions
def get_plan_info(plan_key: str) -> Dict:
    """Get subscription plan information"""
    return SUBSCRIPTION_PLANS.get(plan_key, SUBSCRIPTION_PLANS["free"])

def can_user_access_language(user: User, language: str) -> bool:
    """Check if user's plan allows access to a language"""
    plan = get_plan_info(user.subscription_tier.value)
    return language in plan["languages"]

def can_user_submit_job(user: User) -> tuple[bool, str]:
    """Check if user can submit another job"""
    plan = get_plan_info(user.subscription_tier.value)
    
    if user.total_jobs_this_month >= user.monthly_job_limit:
        return False, f"Monthly limit of {user.monthly_job_limit} jobs exceeded. Upgrade your plan to continue."
    
    return True, "OK"

def get_user_plan_details(user: User) -> Dict:
    """Get detailed plan information for a user"""
    plan = get_plan_info(user.subscription_tier.value)
    
    return {
        "plan": user.subscription_tier.value,
        "plan_name": plan["name"],
        "monthly_price": plan["price"],
        "jobs_used": user.total_jobs_this_month,
        "jobs_limit": user.monthly_job_limit,
        "jobs_remaining": user.monthly_job_limit - user.total_jobs_this_month,
        "languages": plan["languages"],
        "priority": plan["priority"],
        "subscription_end": user.subscription_end_date
    }
