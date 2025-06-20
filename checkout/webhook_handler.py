from django.http import HttpResponse

class StripeWebhookHandler:
    def __init__(self, request):
        self.request = request


    def handle_event(self, event):
        return HttpResponse(
            content=f'Unhandled Webhook recieved {event["type"]}',
            status=200)
    
    def handle_payment_intent_succeeded(self, event):
        return HttpResponse(
            content=f'Payment Intent Succeeded Webhook recieved {event["type"]}',
            status=200)
    
    def handle_payment_intent_failed(self, event):
        return HttpResponse(
            content=f'Payment Intent Failed Webhook recieved {event["type"]}',
            status=200)
    
