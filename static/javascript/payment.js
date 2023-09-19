const public_key = new URLSearchParams(window.location.search).get("public_key")

const stripe = Stripe(public_key);
const client_secret = new URLSearchParams(window.location.search).get("client_secret")
const telegram = new URLSearchParams(window.location.search).get("telegram")
const chat_id = new URLSearchParams(window.location.search).get("chat_id")
const options = {
		clientSecret: client_secret
};

const elements = stripe.elements(options);

const paymentForm = elements.create('payment');

paymentForm.mount('#payment-element');

const form = document.getElementById("payment-form");
form.addEventListener("submit", async (event) => {
	event.preventDefault();

	stripe.confirmPayment({
		elements,
		confirmParams:{
			return_url:`http://127.0.0.1:5000/success?telegram=${telegram}&chat_id=${chat_id}`
		},
	}).then(function(result) {
				if (result.error){
						let error_message=document.getElementById('error-message')
						switch (result.error.type){
								case "invalid_request_error":
									error_message.innerText = "Your card was declined by issuer!"
									break;
								case "validation_error":
									error_message.innerText = "Your card is incorrect format!"
									break;
								default:
									error_message.innerText = "Something went wrong!"
								
						};
					};
		})
	
});
