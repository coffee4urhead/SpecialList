import * as dotenv from 'dotenv';
import getCookie from "../utils.js";
import {loadStripe} from "@stripe/stripe-js";

dotenv.config();

let stripe;
(async () => {
    stripe = await loadStripe(process.env.STRIPE_PUBLIC_KEY);
    if (typeof Stripe === 'undefined') {
        console.error('Stripe.js failed to load properly');
        const script = document.createElement('script');
        script.src = 'https://js.stripe.com/v3/';
        script.onload = initializeBookingHandlers;
        document.head.appendChild(script);
    } else {
        initializeBookingHandlers();
    }
    initializeBookingHandlers();
})();

function initializeBookingHandlers() {
    document.querySelectorAll('.availability-table td[data-slot-id]').forEach(cell => {
        if (cell.textContent.trim() === 'Available') {
            cell.style.cursor = 'pointer';
            cell.addEventListener('click', function () {
                const slotId = this.dataset.slotId;
                const serviceId = document.querySelector('#extended-service-info-container').dataset.serviceId;
                showBookingModal(slotId, serviceId);
            });
        }
    });

    document.querySelector('.modal .close').addEventListener('click', function () {
        document.getElementById('booking-modal').style.display = 'none';
    });

    document.getElementById('proceed-to-payment').addEventListener('click', async function () {
        const slotId = document.getElementById('selected-slot').value;
        const serviceId = document.getElementById('selected-service').value;

        try {
            document.getElementById('booking-form').style.display = 'none';
            document.getElementById('payment-flow').style.display = 'block';

            await bookTimeSlot(slotId, serviceId);
        } catch (error) {
            console.error('Error:', error);
            alert('Payment failed: ' + error.message);
            document.getElementById('booking-form').style.display = 'block';
            document.getElementById('payment-flow').style.display = 'none';
        }
    });
}

function showBookingModal(slotId, serviceId) {
    const modal = document.getElementById('booking-modal');
    document.getElementById('selected-slot').value = slotId;
    document.getElementById('selected-service').value = serviceId;
    modal.style.display = 'block';
}

async function bookTimeSlot(slotId, serviceId) {
    try {
        const bookingResponse = await fetch('/bookings/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                time_slot: slotId,
                service: serviceId,
                notes: document.querySelector('#booking-form textarea').value
            })
        });

        const bookingData = await bookingResponse.json();

        if (!bookingData.success) {
            throw new Error('Booking creation failed');
        }

        const paymentResponse = await fetch(`/payments/create-intent/${bookingData.booking_id}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            }
        });

        const paymentData = await paymentResponse.json();

        const elements = stripe.elements({
            appearance: {
                theme: 'stripe',
                variables: {
                    colorPrimary: '#4CAF50',
                    colorBackground: '#ffffff',
                    colorText: '#32325d',
                }
            }
        });

        const paymentElementContainer = document.getElementById('payment-element');
        paymentElementContainer.innerHTML = '';

        const paymentElement = elements.create('payment');
        paymentElement.mount('#payment-element');

        document.getElementById('submit-payment').onclick = async (e) => {
            e.preventDefault();
            const {error} = await stripe.confirmPayment({
                elements,
                clientSecret: paymentData.clientSecret,
                confirmParams: {
                    return_url: `${window.location.origin}/booking-confirmed/${bookingData.booking_id}/`,
                    receipt_email: document.querySelector('#booking-form [name="email"]')?.value || undefined,
                },
            });

            if (error) {
                throw error;
            }
        };

    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}