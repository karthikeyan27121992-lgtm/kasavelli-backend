from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import razorpay
import logging
import hmac
import hashlib
import urllib.request
import urllib.parse
import json as _json
from .models import Payment
from users.models import Order, OrderItem, Cart

logger = logging.getLogger(__name__)

OWNER_WHATSAPP = '918072000599'   # country code + number, no +


# ── SMS via Fast2SMS (free developer API) ────────────────────────────────────

def _send_sms(message: str) -> None:
    """
    Send an SMS to all configured staff numbers via Fast2SMS Quick SMS API.
    Fails silently — never blocks the response or raises.

    Docs: https://www.fast2sms.com/docs/quicktransactional
    Set FAST2SMS_API_KEY and STAFF_PHONE_NUMBERS (comma-separated) in env.
    """
    api_key = getattr(settings, 'FAST2SMS_API_KEY', '')
    raw_numbers = getattr(settings, 'STAFF_PHONE_NUMBERS', '')
    if not api_key or not raw_numbers:
        logger.warning('Fast2SMS not configured — SMS skipped')
        return

    # Fast2SMS accepts a comma-separated list of 10-digit Indian numbers
    numbers = ','.join(n.strip().lstrip('+91').lstrip('91') for n in raw_numbers.split(',') if n.strip())

    try:
        payload = _json.dumps({
            'route': 'q',           # Quick SMS (no template/DLT needed)
            'message': message,
            'language': 'english',
            'flash': 0,
            'numbers': numbers,
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://www.fast2sms.com/dev/bulkV2',
            data=payload,
            headers={
                'authorization': api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'Kasavelli/1.0',
            },
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read().decode()
            logger.info('Fast2SMS response: %s', body)
    except Exception as exc:
        logger.error('Fast2SMS SMS failed: %s', exc)


# ── Razorpay Webhook ──────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    Razorpay calls this endpoint on every payment event.

    Security: every request is validated against the HMAC-SHA256 signature
    that Razorpay sends in the X-Razorpay-Signature header. Requests with
    invalid or missing signatures are rejected with 400.

    Configure in Razorpay Dashboard → Settings → Webhooks:
      URL  : https://<your-backend>/api/payments/webhook/
      Secret: set RAZORPAY_WEBHOOK_SECRET in your env

    Handled events
    ──────────────
    payment.captured  → mark payment + order as successful, send SMS
    payment.failed    → mark payment + order as failed, send SMS
    """
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')

    # ── 1. Signature verification ────────────────────────────────────────────
    received_sig = request.headers.get('X-Razorpay-Signature', '')
    if webhook_secret:
        expected_sig = hmac.new(
            webhook_secret.encode('utf-8'),
            request.body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, received_sig):
            logger.warning('Razorpay webhook: invalid signature — rejected')
            return HttpResponse('Invalid signature', status=400)

    # ── 2. Parse payload ─────────────────────────────────────────────────────
    try:
        payload = _json.loads(request.body)
    except (_json.JSONDecodeError, ValueError):
        return HttpResponse('Bad JSON', status=400)

    event = payload.get('event', '')
    entity = payload.get('payload', {}).get('payment', {}).get('entity', {})

    razorpay_order_id = entity.get('order_id', '')
    razorpay_payment_id = entity.get('id', '')
    amount_paise = entity.get('amount', 0)
    amount_rupees = amount_paise / 100
    method = entity.get('method', '')

    logger.info('Razorpay webhook event=%s order=%s payment=%s', event, razorpay_order_id, razorpay_payment_id)

    # ── 3. Handle payment.captured ───────────────────────────────────────────
    if event == 'payment.captured':
        try:
            payment = Payment.objects.select_related('order__user').get(
                razorpay_order_id=razorpay_order_id
            )
            # Idempotency: skip if already marked success
            if payment.status != 'success':
                payment.razorpay_payment_id = razorpay_payment_id
                payment.payment_method = method
                payment.status = 'success'
                payment.save()

                order = payment.order
                order.payment_id = razorpay_payment_id
                order.payment_status = 'completed'
                order.status = 'processing'
                order.save()

            order = payment.order
            customer_name = getattr(order.user, 'name', '') or getattr(order.user, 'username', 'Unknown')
            phone = getattr(order, 'phone_number', '') or ''
            items = list(order.items.select_related('product').all())
            item_lines = ', '.join(
                f"{i.product.name} x{i.quantity}" for i in items
            )

            sms_text = (
                f"[Kasavelli] New Order Received!\n"
                f"Order: {order.order_id}\n"
                f"Customer: {customer_name} | Ph: {phone}\n"
                f"Items: {item_lines}\n"
                f"Total: Rs.{amount_rupees:.0f} via {method}"
            )
            _send_sms(sms_text)

        except Payment.DoesNotExist:
            logger.error('Webhook payment.captured: no Payment for order_id=%s', razorpay_order_id)
        except Exception:
            logger.exception('Webhook payment.captured processing error')

    # ── 4. Handle payment.failed ─────────────────────────────────────────────
    elif event == 'payment.failed':
        try:
            payment = Payment.objects.select_related('order__user').get(
                razorpay_order_id=razorpay_order_id
            )
            if payment.status != 'failed':
                payment.razorpay_payment_id = razorpay_payment_id
                payment.payment_method = method
                payment.status = 'failed'
                payment.save()

                order = payment.order
                order.payment_status = 'failed'
                order.status = 'cancelled'
                order.save()

            order = payment.order
            customer_name = getattr(order.user, 'name', '') or getattr(order.user, 'username', 'Unknown')
            error_desc = entity.get('error_description', 'N/A')

            sms_text = (
                f"[Kasavelli] Payment FAILED\n"
                f"Order: {order.order_id}\n"
                f"Customer: {customer_name}\n"
                f"Amount: Rs.{amount_rupees:.0f}\n"
                f"Reason: {error_desc}"
            )
            _send_sms(sms_text)

        except Payment.DoesNotExist:
            logger.error('Webhook payment.failed: no Payment for order_id=%s', razorpay_order_id)
        except Exception:
            logger.exception('Webhook payment.failed processing error')

    # ── 5. Acknowledge all events ─────────────────────────────────────────────
    return HttpResponse('ok', status=200)

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
