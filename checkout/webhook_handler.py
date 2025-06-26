from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order, OrderLineItem
from products.models import Product
from profiles.models import UserProfile

import json
import stripe
import time
import traceback

class StripeWebhookHandler:
    def __init__(self, request):
        self.request = request

    def _send_confirmation_email(self, order):
        cust_email = order.email
        subject = render_to_string(
            'checkout/conf_email/confirmation_email_subject.txt',
            {'order': order}
            )
        body = render_to_string(
            'checkout/conf_email/confirmation_email_body.txt',
            {'order': order, 'contact_email': settings.DEFAULT_FROM_EMAIL}
        )
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [cust_email],
        )

    def handle_event(self, event):
        return HttpResponse(
            content=f'Unhandled Webhook recieved {event["type"]}',
            status=200)
    
    def handle_payment_intent_succeeded(self, event):
        intent = event.data.object
        pid = intent.id
        metadata = intent.metadata
        bag = metadata.get('bag')
        save_info = metadata.get('save_info')

        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe_charge = stripe.Charge.retrieve(intent.latest_charge)
        billing_details = stripe_charge.billing_details
        shipping_details = intent.shipping or {}
        shipping_address = shipping_details.address or {}

        grand_total = round(stripe_charge.amount / 100, 2)

        print(intent)
        print(f"Billing Details: {billing_details}")
        print(f"Shipping Details: {shipping_details}")
        print(f"Grand Total: {grand_total}")

        # Clean empty shipping address fields
        for field, value in shipping_address.items():
            if value == "":
                shipping_address[field] = None

        # --- NEW: Robust email extraction ---
        email = billing_details.email or metadata.get("email") or intent.receipt_email

        # Fallback: if still no email, try charge billing details again just in case
        if not email and intent.latest_charge:
            try:
                charge = stripe.Charge.retrieve(intent.latest_charge)
                email = charge.billing_details.email
            except Exception as e:
                print(f"Error retrieving charge email fallback: {e}")

        print(f"Resolved email: {email}")
        # -----------------------------------

        profile = None
        username = metadata.get('username', None)
        if username and username != "AnonymousUser":
            try:
                profile = UserProfile.objects.get(user__username=username)
                if save_info:
                    profile.default_phone_number = shipping_details.get('phone')
                    profile.default_country = shipping_address.get('country')
                    profile.default_postcode = shipping_address.get('postal_code')
                    profile.default_town_or_city = shipping_address.get('city')
                    profile.default_street_address1 = shipping_address.get('line1')
                    profile.default_street_address2 = shipping_address.get('line2')
                    profile.default_county = shipping_address.get('state')
                    profile.save()
            except UserProfile.DoesNotExist:
                profile = None  # Continue without user profile

        order_exists = False
        attempt = 1
        while attempt <= 5:
            try:
                order = Order.objects.get(
                    full_name__iexact=shipping_details.name,
                    user_profile=profile,
                    email__iexact=email,
                    phone_number__iexact=shipping_details.get('phone'),
                    country__iexact=shipping_address.get('country'),
                    postcode__iexact=shipping_address.get('postal_code'),
                    town_or_city__iexact=shipping_address.get('city'),
                    street_address1__iexact=shipping_address.get('line1'),
                    street_address2__iexact=shipping_address.get('line2'),
                    county__iexact=shipping_address.get('state'),
                    grand_total__iexact=grand_total,
                    original_bag=bag,
                    stripe_pid=pid,
                )
                order_exists = True
                break
            except Order.DoesNotExist:
                attempt += 1
                time.sleep(1)

        if order_exists:
            self._send_confirmation_email(order)
            return HttpResponse(
                content=f'Webhook received {event["type"]} | SUCCESS: Verified order already in database',
                status=200
            )

        order = None
        print("billing_details.email:", billing_details.email)
        print("metadata email:", metadata.get("email"))
        print("intent.receipt_email:", intent.receipt_email)
        try:
            order = Order.objects.create(
                full_name=shipping_details.name,
                user_profile=profile,
                email=email,
                phone_number=shipping_details.get('phone'),
                country=shipping_address.get('country'),
                postcode=shipping_address.get('postal_code'),
                town_or_city=shipping_address.get('city'),
                street_address1=shipping_address.get('line1'),
                street_address2=shipping_address.get('line2'),
                county=shipping_address.get('state'),
                original_bag=bag,
                stripe_pid=pid,
            )
            for item_id, item_data in json.loads(bag).items():
                product = Product.objects.get(id=item_id)
                if isinstance(item_data, int):
                    OrderLineItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item_data,
                    )
                else:
                    for size, quantity in item_data['items_by_size'].items():
                        OrderLineItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            product_size=size,
                        )
        except Exception as e:
            print("Webhook exception:", e)
            traceback.print_exc()
            if order:
                order.delete()
            return HttpResponse(
                content=f'Webhook received {event["type"]} | ERROR: {e}',
                status=500
            )

        self._send_confirmation_email(order)
        return HttpResponse(
            content=f'Webhook received {event["type"]} | SUCCESS: Order created in webhook',
            status=200
        )


    def handle_payment_intent_failed(self, event):
        return HttpResponse(
            content=f'Webhook recieved {event["type"]}',
            status=200)
    
