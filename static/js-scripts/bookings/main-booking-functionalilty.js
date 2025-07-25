import getCookie from "../utils.js";
import { loadStripe } from 'https://cdn.skypack.dev/@stripe/stripe-js';

let stripe;
let elements;
let clientSecret;

function getServiceIdFromUrl() {
    const segments = window.location.pathname.split('/').filter(Boolean);
    return segments[segments.length - 1];
}

document.addEventListener('DOMContentLoaded', async () => {
    stripe = await loadStripe(STRIPE_PUBLIC_KEY);
    if (!stripe) {
        console.error('Stripe.js failed to load properly');
        const script = document.createElement('script');
        script.src = 'https://js.stripe.com/v3/';
        script.onload = initializeBookingHandlers;
        document.head.appendChild(script);
    } else {
        initializeBookingHandlers();
    }
});

function initializeBookingHandlers() {
    const serviceId = getServiceIdFromUrl();

    document.querySelectorAll('.availability-table td[data-slot-id]').forEach(cell => {
        if (cell.textContent.trim().toLowerCase() === 'available') {
            cell.style.cursor = 'pointer';
            cell.addEventListener('click', () => {
                const slotId = cell.dataset.slotId;
                showBookingModal(slotId, serviceId);
            });
        }
    });

    const modal = document.getElementById('booking-modal');
    if (!modal) return console.error('Modal element not found');

    const closeBtn = modal.querySelector('.close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
            resetPaymentFlow();
        });
    }

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            resetPaymentFlow();
        }
    });

    const paymentForm = document.getElementById('payment-form');
    if (paymentForm) {
        paymentForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const submitBtn = document.getElementById('submit-button');
            const messageContainer = document.getElementById('payment-message');

            if (submitBtn) submitBtn.disabled = true;
            if (messageContainer) {
                messageContainer.textContent = '';
                messageContainer.classList.add('hidden');
            }

            const { error } = await stripe.confirmPayment({
                elements,
                confirmParams: {
                    return_url: `${window.location.origin}/booking-confirmed/${document.getElementById('selected-slot').value}/`,
                    receipt_email: document.querySelector('#booking-form [name="email"]').value,
                },
            });

            if (error && messageContainer) {
                messageContainer.textContent = error.message;
                messageContainer.classList.remove('hidden');
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    }

    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const slotId = document.getElementById('selected-slot')?.value;
            const serviceId = getServiceIdFromUrl();

            try {
                e.target.querySelector('button[type="submit"]').disabled = true;

                await bookTimeSlot(slotId, serviceId);

                bookingForm.style.display = 'none';
                const paymentForm = document.getElementById('payment-form');
                if (paymentForm) paymentForm.style.display = 'block';
            } catch (error) {
                alert('Booking failed: ' + error.message);
                bookingForm.style.display = 'block';
                e.target.querySelector('button[type="submit"]').disabled = false;
            }
        });
    }
}

function showBookingModal(slotId, serviceId) {
    const modal = document.getElementById('booking-modal');
    if (!modal) return;
    const selectedSlot = document.getElementById('selected-slot');
    const selectedService = document.getElementById('selected-service');
    if (selectedSlot) selectedSlot.value = slotId;
    if (selectedService) selectedService.value = serviceId;
    modal.style.display = 'block';
    resetPaymentFlow();
}

function resetPaymentFlow() {
    const bookingForm = document.getElementById('booking-form');
    const paymentForm = document.getElementById('payment-form');
    const paymentMessage = document.getElementById('payment-message');
    const submitBtn = document.getElementById('submit-button');

    if (bookingForm) bookingForm.style.display = 'block';
    if (paymentForm) paymentForm.style.display = 'none';
    if (paymentMessage) {
        paymentMessage.textContent = '';
        paymentMessage.classList.add('hidden');
    }
    if (submitBtn) submitBtn.disabled = false;
    if (elements) {
        const paymentElement = elements.getElement('payment');
        if (paymentElement) paymentElement.unmount();
    }
    clientSecret = null;
    elements = null;
}

async function bookTimeSlot(slotId, serviceId) {
    const bookingResponse = await fetch('/booking/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            time_slot: slotId,
            service: serviceId,
            notes: document.querySelector('#booking-form textarea')?.value || '',
            email: document.querySelector('#booking-form [name="email"]')?.value || ''
        })
    });
    if (!bookingResponse.ok) throw new Error('Booking creation failed');
    const bookingData = await bookingResponse.json();

    const paymentResponse = await fetch(`/booking/payments/create-intent/${bookingData.booking_id}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    });
    if (!paymentResponse.ok) throw new Error('Payment intent creation failed');
    const paymentData = await paymentResponse.json();

    clientSecret = paymentData.clientSecret;

    elements = stripe.elements({
        clientSecret,
        appearance: {
            theme: 'stripe',
            variables: {
                colorPrimary: '#4CAF50',
                colorBackground: '#ffffff',
                colorText: '#32325d',
            }
        }
    });

    const paymentElement = elements.create('payment');
    paymentElement.mount('#payment-element');
}
