from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from models.types import Member
from utils.dependencies import get_current_user
from pydantic import BaseModel
import stripe
import os
from typing import Optional
from datetime import datetime, timedelta
import calendar

router = APIRouter()

# Initialize Stripe with your secret key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY environment variable is required")

YOUR_DOMAIN = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Request models
class SetupPaymentMethodRequest(BaseModel):
    quantity: int = 1  # For initial setup, can be minimal amount

class CreatePortalSessionRequest(BaseModel):
    customer_id: Optional[str] = None

class UsageRecord(BaseModel):
    trucks_used: int
    date_used: str
    description: Optional[str] = None

class BillingUsageRequest(BaseModel):
    trucks_used: int
    period: str  # e.g., "2024-01"

# Setup payment method for monthly billing
@router.post("/setup-payment-method")
async def setup_payment_method(
    request: SetupPaymentMethodRequest,
    current_user: Member = Depends(get_current_user)
):
    try:
        # Check if customer already exists
        customers = stripe.Customer.list(
            email=current_user.email,
            limit=1
        )

        if customers.data:
            customer = customers.data[0]
        else:
            # Create new customer
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
                metadata={
                    'user_id': str(current_user.id),
                    'company_code': current_user.account.company_code if current_user.account else '',
                }
            )

        # Create setup intent for payment method
        setup_intent = stripe.SetupIntent.create(
            customer=customer.id,
            usage='off_session',  # For future payments
            payment_method_types=['card'],
        )

        # Create a minimal checkout session to collect payment method
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='setup',  # Setup mode for collecting payment method
            customer=customer.id,
            success_url=f'{YOUR_DOMAIN}/dashboard/settings?success=true&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{YOUR_DOMAIN}/dashboard/settings?canceled=true',
            metadata={
                'user_id': str(current_user.id),
                'user_email': current_user.email,
                'setup_type': 'payment_method'
            }
        )

        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
            "customer_id": customer.id
        }
    except Exception as e:
        print(f"Error setting up payment method: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup payment method")

# Record truck usage (this would be called when user loads trucks)
@router.post("/record-usage")
async def record_usage(
    request: UsageRecord,
    current_user: Member = Depends(get_current_user)
):
    try:
        # In a real implementation, you'd store this in your database
        # For now, we'll store it as a Stripe invoice item for the current billing period

        # Get customer
        customers = stripe.Customer.list(
            email=current_user.email,
            limit=1
        )

        if not customers.data:
            raise HTTPException(status_code=400, detail="No payment method setup. Please connect a payment method first.")

        customer = customers.data[0]

        # Add usage record as invoice item
        stripe.InvoiceItem.create(
            customer=customer.id,
            amount=request.trucks_used * 2500,  # $25.00 per truck in cents
            currency='usd',
            description=f"Load Plan Pro - {request.trucks_used} trucks loaded on {request.date_used}",
            metadata={
                'user_id': str(current_user.id),
                'trucks_used': str(request.trucks_used),
                'date_used': request.date_used,
                'type': 'usage'
            }
        )

        return {"status": "success", "trucks_recorded": request.trucks_used}
    except Exception as e:
        print(f"Error recording usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to record usage")

# Create monthly invoice and charge customer
@router.post("/create-monthly-invoice")
async def create_monthly_invoice(
    request: BillingUsageRequest,
    current_user: Member = Depends(get_current_user)
):
    try:
        # Get customer
        customers = stripe.Customer.list(
            email=current_user.email,
            limit=1
        )

        if not customers.data:
            raise HTTPException(status_code=400, detail="No customer found")

        customer = customers.data[0]

        # Create invoice for the period
        invoice = stripe.Invoice.create(
            customer=customer.id,
            description=f"Load Plan Pro usage for {request.period}",
            metadata={
                'billing_period': request.period,
                'user_id': str(current_user.id)
            }
        )

        # Finalize and pay the invoice
        invoice = stripe.Invoice.finalize_invoice(invoice.id)
        invoice = stripe.Invoice.pay(invoice.id)

        return {
            "invoice_id": invoice.id,
            "amount": invoice.amount_paid / 100,
            "status": invoice.status
        }
    except Exception as e:
        print(f"Error creating monthly invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to create monthly invoice")

# Create customer portal session
@router.post("/create-portal-session")
async def create_portal_session(
    request: CreatePortalSessionRequest,
    current_user: Member = Depends(get_current_user)
):
    try:
        # Get customer by email if no customer_id provided
        if request.customer_id:
            customer_id = request.customer_id
        else:
            customers = stripe.Customer.list(
                email=current_user.email,
                limit=1
            )

            if not customers.data:
                raise HTTPException(status_code=400, detail="No customer found. Please setup a payment method first.")

            customer_id = customers.data[0].id

        # Create billing portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f'{YOUR_DOMAIN}/dashboard/settings',
        )

        return {"portal_url": portal_session.url}
    except Exception as e:
        print(f"Error creating portal session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

# Get payment/billing history for the current user
@router.get("/payment-history")
async def get_payment_history(current_user: Member = Depends(get_current_user)):
    try:
        # Get customer
        customers = stripe.Customer.list(
            email=current_user.email,
            limit=1
        )

        if not customers.data:
            return {"payments": []}

        customer = customers.data[0]

        # Get invoices (monthly bills)
        invoices = stripe.Invoice.list(
            customer=customer.id,
            limit=12  # Last 12 months
        )

        user_payments = []
        for invoice in invoices.data:
            if invoice.status == 'paid':
                # Calculate trucks from invoice amount
                trucks_count = int(invoice.amount_paid / 2500) if invoice.amount_paid > 0 else 0

                user_payments.append({
                    'id': invoice.id,
                    'amount': invoice.amount_paid / 100,
                    'currency': invoice.currency.upper(),
                    'status': 'succeeded',
                    'created': invoice.created,
                    'trucks_purchased': trucks_count,
                    'description': invoice.description or f"Load Plan Pro - {trucks_count} trucks",
                    'period_start': invoice.period_start,
                    'period_end': invoice.period_end
                })

        return {"payments": user_payments}
    except Exception as e:
        print(f"Error retrieving payment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment history")

# Get current usage data and billing info
@router.get("/usage-data")
async def get_usage_data(current_user: Member = Depends(get_current_user)):
    try:
        # Get customer
        customers = stripe.Customer.list(
            email=current_user.email,
            limit=1
        )

        if not customers.data:
            return {
                "current_month_trucks": 0,
                "total_trucks_loaded": 0,
                "current_month_cost": 0,
                "total_spent": 0,
                "price_per_truck": 25.00,
                "payment_method_connected": False,
                "last_payment_date": None,
                "next_billing_date": None
            }

        customer = customers.data[0]

        # Check if customer has a payment method
        payment_methods = stripe.PaymentMethod.list(
            customer=customer.id,
            type='card'
        )

        has_payment_method = len(payment_methods.data) > 0

        # Get current month usage from pending invoice items
        current_date = datetime.now()
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Get pending invoice items for this month
        invoice_items = stripe.InvoiceItem.list(
            customer=customer.id,
            limit=100
        )

        current_month_trucks = 0
        current_month_cost = 0

        for item in invoice_items.data:
            item_date = datetime.fromtimestamp(item.date)
            if (item_date >= start_of_month and
                item.metadata and
                item.metadata.get('type') == 'usage'):
                trucks = int(item.metadata.get('trucks_used', '0'))
                current_month_trucks += trucks
                current_month_cost += item.amount / 100

        # Get total historical data from invoices
        invoices = stripe.Invoice.list(
            customer=customer.id,
            limit=100
        )

        total_trucks_loaded = current_month_trucks
        total_spent = current_month_cost
        last_payment_date = None

        for invoice in invoices.data:
            if invoice.status == 'paid':
                trucks = int(invoice.amount_paid / 2500) if invoice.amount_paid > 0 else 0
                total_trucks_loaded += trucks
                total_spent += invoice.amount_paid / 100

                if not last_payment_date or invoice.created > last_payment_date:
                    last_payment_date = invoice.created

        # Calculate next billing date (first of next month)
        if current_date.month == 12:
            next_billing_date = datetime(current_date.year + 1, 1, 1)
        else:
            next_billing_date = datetime(current_date.year, current_date.month + 1, 1)

        return {
            "current_month_trucks": current_month_trucks,
            "total_trucks_loaded": total_trucks_loaded,
            "current_month_cost": current_month_cost,
            "total_spent": total_spent,
            "price_per_truck": 25.00,
            "payment_method_connected": has_payment_method,
            "last_payment_date": last_payment_date,
            "next_billing_date": int(next_billing_date.timestamp())
        }
    except Exception as e:
        print(f"Error retrieving usage data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage data")

# Disconnect payment method
@router.post("/disconnect-payment-method")
async def disconnect_payment_method(current_user: Member = Depends(get_current_user)):
    try:
        # Get customer
        customers = stripe.Customer.list(
            email=current_user.email,
            limit=1
        )

        if not customers.data:
            return {"status": "no_customer_found"}

        customer = customers.data[0]

        # Detach all payment methods
        payment_methods = stripe.PaymentMethod.list(
            customer=customer.id,
            type='card'
        )

        for pm in payment_methods.data:
            stripe.PaymentMethod.detach(pm.id)

        return {"status": "success", "message": "Payment method disconnected"}
    except Exception as e:
        print(f"Error disconnecting payment method: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect payment method")

# Webhook endpoint for Stripe events
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_12345')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        print(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        print(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'setup_intent.succeeded':
        setup_intent = event['data']['object']
        print(f'Payment method setup succeeded for customer {setup_intent["customer"]}')

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        print(f'Monthly payment succeeded for {invoice["amount_paid"]} cents')

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        print(f'Monthly payment failed for {invoice["amount_due"]} cents')

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        print(f'Customer {subscription["customer"]} cancelled subscription')

    else:
        print(f'Unhandled event type: {event["type"]}')

    return {"status": "success"}

# Backward compatibility - redirect to setup payment method
@router.post("/create-checkout-session")
async def create_checkout_session(
    request: SetupPaymentMethodRequest,
    current_user: Member = Depends(get_current_user)
):
    return await setup_payment_method(request, current_user)

# Backward compatibility - redirect to usage data
@router.get("/truck-credits")
async def get_truck_credits(current_user: Member = Depends(get_current_user)):
    usage_data = await get_usage_data(current_user)
    return {
        "total_trucks_purchased": usage_data["total_trucks_loaded"],
        "total_spent": usage_data["total_spent"],
        "available_credits": usage_data["current_month_trucks"],
        "price_per_truck": usage_data["price_per_truck"]
    }
