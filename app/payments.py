import stripe

stripe.api_key = "sk_test_51NXNWlEeYaoViK2088VnS3XyYuGGu3Q1hbS8taHBByxJpv06EkEAZXXb76ovOsymZK9DD85PPzkboAZapdCjPkiz00fQOxPzJo"
public_key = "pk_test_51NXNWlEeYaoViK20FSKOMCDS0vrKG4NugYh9I0C81vSYNeWwVM39bZajEy2N3shjmEy3edAIntqqByUv0T7DsDyc00rFbrQUAd"


def get_payment_intent(amount: int, currency: str):
    payment_intent = stripe.PaymentIntent.create(amount=amount*100, currency=currency,
                                                 payment_method_types=["card"])
    return payment_intent
