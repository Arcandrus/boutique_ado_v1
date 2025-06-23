import stripe
from django.conf import settings
from django.http import HttpResponse

class StripeWebhookHandler:
    def __init__(self, request):
        self.request = request


    def handle_event(self, event):
        return HttpResponse(
            content=f'Unhandled Webhook recieved {event["type"]}',
            status=200)
    
    def handle_payment_intent_succeeded(self, event):
        intent = event.data.object
        pid = intent.id
        bag = intent.metadata.bag
        save_info = intent.metadata.save_info

        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe_charge = stripe.Charge.retrieve(intent.latest_charge)
        billing_details = stripe_charge.billing_details
        shipping_details = intent.shipping

        grand_total = round(stripe_charge.amount / 100, 2)

        # Print details to verify
        print(intent)
        print(f"Billing Details: {billing_details}")
        print(f"Shipping Details: {shipping_details}")
        print(f"Grand Total: {grand_total}")

        return HttpResponse(
            content=f'Webhook received {event["type"]}',
            status=200
        )
    
    def handle_payment_intent_failed(self, event):
        return HttpResponse(
            content=f'Webhook recieved {event["type"]}',
            status=200)
    
