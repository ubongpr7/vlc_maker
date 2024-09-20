

from django.shortcuts import render
from djstripe.models import Product
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from djstripe.settings import djstripe_settings



from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from djstripe.settings import djstripe_settings
from djstripe.models import Subscription

import stripe

@login_required
def subscription_confirm(request):
    # set our stripe keys up
    stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY

    # get the session id from the URL and retrieve the session object from Stripe
    session_id = request.GET.get("session_id")
    session = stripe.checkout.Session.retrieve(session_id)

    # get the subscribing user from the client_reference_id we passed in above
    client_reference_id = int(session.client_reference_id)
    subscription_holder = get_user_model().objects.get(id=client_reference_id)
    # sanity check that the logged in user is the one being updated
    assert subscription_holder == request.user

    # get the subscription object form Stripe and sync to djstripe
    subscription = stripe.Subscription.retrieve(session.subscription)
    djstripe_subscription = Subscription.sync_from_stripe_data(subscription)

    # set the subscription and customer on our user
    subscription_holder.subscription = djstripe_subscription
    subscription_holder.customer = djstripe_subscription.customer
    subscription_holder.save()

    # show a message to the user and redirect
    messages.success(request, f"You've successfully signed up. Thanks for the support!")
    return HttpResponseRedirect(reverse("subscription_details"))



@login_required
@require_POST
def create_portal_session(request):
    stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY
    portal_session = stripe.billing_portal.Session.create(
        customer=request.user.customer.id,
        return_url="http://153.92.208.98:8000/text/",
    )
    return HttpResponseRedirect(portal_session.url)


@login_required
def embedded_pricing_page(request):
    return render(request, 'accounts/embedded_stripe.html', {
        'stripe_public_key': djstripe_settings.STRIPE_PUBLIC_KEY,
        'stripe_pricing_table_id': settings.STRIPE_PRICING_TABLE_ID,
    })

def pricing_page(request):
    return render(request, 'pricing_page.html', {
        'products': Product.objects.all()
    })




# class PaymentAPI(APIView):
#     serializer_class = CardInformationSerializer

#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#         response = {}
#         if serializer.is_valid():
#             data_dict = serializer.data
          
#       stripe.api_key = 'your-key-goes-here'
#       response = self.stripe_card_payment(data_dict=data_dict)

#         else:
#             response = {'errors': serializer.errors, 'status':
#                 status.HTTP_400_BAD_REQUEST
#                 }
                
#         return Response(response)

#     def stripe_card_payment(self, data_dict):
#         try:
#             card_details = (
#                 type="card",
#                 card={
#                     "number": data_dict['card_number'],
#                     "exp_month": data_dict['expiry_month'],
#                     "exp_year": data_dict['expiry_year'],
#                     "cvc": data_dict['cvc'],
#                 },
#             )
#             #  you can also get the amount from databse by creating a model
#             payment_intent = stripe.PaymentIntent.create(
#                 amount=10000, 
#                 currency='inr',
#             )
#             payment_intent_modified = stripe.PaymentIntent.modify(
#                 payment_intent['id'],
#                 payment_method=card_details['id'],
#             )
#             try:
#                 payment_confirm = stripe.PaymentIntent.confirm(
#                     payment_intent['id']
#                 )
#                 payment_intent_modified = stripe.PaymentIntent.retrieve(payment_intent['id'])
#             except:
#                 payment_intent_modified = stripe.PaymentIntent.retrieve(payment_intent['id'])
#                 payment_confirm = {
#                     "stripe_payment_error": "Failed",
#                     "code": payment_intent_modified['last_payment_error']['code'],
#                     "message": payment_intent_modified['last_payment_error']['message'],
#                     'status': "Failed"
#                 }
#             if payment_intent_modified and payment_intent_modified['status'] == 'succeeded':
#                 response = {
#                     'message': "Card Payment Success",
#                     'status': status.HTTP_200_OK,
#                     "card_details": card_details,
#                     "payment_intent": payment_intent_modified,
#                     "payment_confirm": payment_confirm
#                 }
#             else:
#                 response = {
#                     'message': "Card Payment Failed",
#                     'status': status.HTTP_400_BAD_REQUEST,
#                     "card_details": card_details,
#                     "payment_intent": payment_intent_modified,
#                     "payment_confirm": payment_confirm
#                 }
#         except:
#             response = {
#                 'error': "Your card number is incorrect",
#                 'status': status.HTTP_400_BAD_REQUEST,
#                 "payment_intent": {"id": "Null"},
#                 "payment_confirm": {'status': "Failed"}
#             }
#         return response



