from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import razorpay
import logging
import urllib.request
import urllib.parse
import json as _json
from .models import Payment
from users.models import Order, OrderItem, Cart

logger = logging.getLogger(__name__)

OWNER_WHATSAPP = '918072000599'   # country code + number, no +

def _send_whatsapp_notification(order, items):
    """
    Send an order notification to the owner via the CallMeBot WhatsApp API.
    Falls back silently if the request fails — never blocks the response.
    """
    api_key = getattr(settings, 'CALLMEBOT_API_KEY', '')
    if not api_key:
        logger.warning('CALLMEBOT_API_KEY not set — WhatsApp notification skipped')
        return

    lines = [
        f"🛍 *New Order — Kasavelli*",
        f"Order ID: {order.order_id}",
        f"Customer: {order.user.name} (+91 {order.user.phone_number})",
        f"",
        "*Items Ordered:*",
    ]
    for item in items:
        lines.append(f"• {item.product.name} x{item.quantity} — ₹{item.price * item.quantity}")
    lines += [
        f"",
        f"*Total Paid: ₹{order.total_amount}*",
        f"Ship to: {order.shipping_address}",
        f"Contact: {order.phone_number}",
    ]
    message = '\n'.join(lines)

    try:
        params = urllib.parse.urlencode({
            'phone': OWNER_WHATSAPP,
            'text': message,
            'apikey': api_key,
        })
        url = f'https://api.callmebot.com/whatsapp.php?{params}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Kasavelli/1.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            logger.info('WhatsApp notification sent: %s', resp.status)
    except Exception as exc:
        logger.error('WhatsApp notification failed: %s', exc)


class PaymentViewSet(viewsets.ViewSet):
    """ViewSet for Razorpay payment operations"""
    permission_classes = [IsAuthenticated]

    @property
    def razorpay_client(self):
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    @action(detail=False, methods=['post'])
    def create_order(self, request):
        """Create Razorpay order"""
        try:
            # Guard: Razorpay keys must be configured
            if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                return Response(
                    {'error': 'Payment gateway not configured. Please contact support.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Get cart items
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                return Response(
                    {'error': 'Cart is empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate subtotal
            subtotal = sum(
                item.quantity * float(item.product.discounted_price or item.product.price)
                for item in cart_items
            )

            # Apply shipping
            shipping = 0 if subtotal >= 999 else 99

            # Apply spin-wheel discount if provided and valid
            spin_pct = int(request.data.get('spin_discount_pct', 0) or 0)
            spin_pct = max(0, min(spin_pct, 100))
            # Validate against user's stored spin (prevents tampering)
            user_spin_pct = request.user.spin_discount_pct or 0
            from django.utils import timezone as tz
            user_spin_exp = request.user.spin_discount_expires_at
            if not (user_spin_pct > 0 and user_spin_exp and user_spin_exp > tz.now()):
                spin_pct = 0   # expired or not set — ignore frontend value
            spin_discount = round(subtotal * spin_pct / 100, 2)

            total_amount = round(subtotal + shipping - spin_discount, 2)
            total_amount = max(total_amount, 1)   # minimum ₹1

            # Create Razorpay order (amount in paise)
            razorpay_order = self.razorpay_client.order.create({
                'amount': int(total_amount * 100),
                'currency': 'INR',
                'payment_capture': 1
            })

            # Create order in database
            order = Order.objects.create(
                user=request.user,
                order_id=razorpay_order['id'],
                total_amount=total_amount,
                shipping_address=request.data.get('shipping_address', ''),
                phone_number=request.data.get('phone_number', request.user.phone_number) or request.user.phone_number,
                status='pending'
            )

            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.discounted_price or cart_item.product.price
                )

            # Create payment record
            Payment.objects.create(
                order=order,
                razorpay_order_id=razorpay_order['id'],
                amount=total_amount,
                status='pending'
            )

            return Response({
                'order_id': razorpay_order['id'],
                'amount': float(total_amount),   # cast Decimal → float for JSON
                'currency': 'INR',
                'key': settings.RAZORPAY_KEY_ID
            })

        except Exception as e:
            logger.exception('create_order failed for user %s', request.user)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        """Verify Razorpay payment signature"""
        try:
            razorpay_order_id = request.data.get('razorpay_order_id')
            razorpay_payment_id = request.data.get('razorpay_payment_id')
            razorpay_signature = request.data.get('razorpay_signature')

            # Verify signature using Razorpay's official utility
            client = self.razorpay_client
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })

            # Signature valid — update payment & order
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = 'success'
            payment.save()

            # Update order status
            order = payment.order
            order.payment_id = razorpay_payment_id
            order.payment_status = 'completed'
            order.status = 'processing'
            order.save()

            # Clear cart
            Cart.objects.filter(user=request.user).delete()

            # Send WhatsApp notification to owner (non-blocking)
            order_items = list(order.items.select_related('product').all())
            _send_whatsapp_notification(order, order_items)

            return Response({
                'message': 'Payment verified successfully',
                'order_id': order.order_id
            })
        except razorpay.errors.SignatureVerificationError:
            return Response(
                {'error': 'Invalid payment signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception('verify_payment failed')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def payment_failed(self, request):
        """Handle payment failure"""
        try:
            razorpay_order_id = request.data.get('razorpay_order_id')
            
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            payment.status = 'failed'
            payment.save()
            
            order = payment.order
            order.payment_status = 'failed'
            order.status = 'cancelled'
            order.save()
            
            return Response({'message': 'Payment failure recorded'})
            
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception('payment_failed handler error')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Made with Bob
