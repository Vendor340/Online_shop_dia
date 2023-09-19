const public_key = "pk_test_51NXNWlEeYaoViK20FSKOMCDS0vrKG4NugYh9I0C81vSYNeWwVM39bZajEy2N3shjmEy3edAIntqqByUv0T7DsDyc00rFbrQUAd"

const stripe = Stripe(public_key)

const client_secret = new URLSearchParams(window.location.search).get("payment_intent_client_secret")
const message = document.getElementById("message")
const return_buton = document.getElementById("return_button")

let formElem = document.createElement("form")

let button = document.createElement("button")


const payment_status = stripe.retrievePaymentIntent(client_secret).then(({paymentIntent}) => {
	switch (paymentIntent.status){
		case "succeeded":
			message.innerText = "Payment is successful!"
			formElem.method = "POST"
			button.innerText = "Return to home"
			
			formElem.appendChild(button)
			return_button.appendChild(formElem)
			break;
		case "processing":
			message.innerText = "Payment is processing."
			break;
		default:
			message.innerText = "Your card was declined by issuer!"
			formElem.action = "{{url_for('payment-gateway')}}"
			button.innerText = "Return to payment form"

			formElem.appendChild(button)
			return_button.appendChild(formElem)
			break;
	}
})

