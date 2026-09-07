from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import razorpay
import logging
from .models import Payment
from users.models import Order, OrderItem, Cart

logger = logging.getLogger(__name__)


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
            # Get cart items
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                return Response(
                    {'error': 'Cart is empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate total amount
            total_amount = sum(
                item.quantity * (item.product.discounted_price or item.product.price)
                for item in cart_items
            )

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
                phone_number=request.data.get('phone_number', request.user.phone_number),
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
