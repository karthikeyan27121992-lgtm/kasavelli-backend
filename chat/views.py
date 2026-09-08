import json
import google.generativeai as genai
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# System prompt — tells Gemini exactly who it is and what it knows
SYSTEM_PROMPT = """You are Kasavelli Assistant, a helpful and friendly customer support chatbot for Kasavelli — a premium 925 sterling silver jewellery brand based in India.

About Kasavelli:
- Founded in 2024, handcrafted in India
- Specialises in 925 hallmarked sterling silver jewellery
- Product categories: Chains with Pendants, Earrings, Rings, Bracelets, Anklets, Pendants, Gold Polish Looks
- All jewellery is hypoallergenic and safe for sensitive skin
- Prices range from ₹300 to ₹5000 depending on design and weight

Policies:
- Free shipping on orders above ₹999
- 30-day easy return policy (unworn, original condition)
- Cash on delivery and online payment (Razorpay) accepted
- Delivery in 5-7 business days across India

Silver care tips:
- Store in an airtight box or zip-lock bag to prevent tarnishing
- Clean with a soft dry cloth or mild soap and water
- Avoid contact with perfume, sweat, and chemicals
- Remove before swimming or bathing

Your role:
- Answer questions about products, categories, pricing, shipping, returns, and silver care
- Help customers pick the right jewellery for occasions (wedding, gifting, daily wear)
- Be warm, concise, and helpful — like a knowledgeable store assistant
- If you don't know a specific product's price or availability, say so and suggest they browse the website
- Keep responses short (2–4 sentences max) unless the user asks for detailed information
- Always respond in the same language the user writes in (English or Tamil or Hindi)
- Never make up specific product names or prices
- Sign off with "— Kasavelli Assistant 💎" only on the first message
"""


@csrf_exempt
@require_http_methods(["POST"])
def chat_view(request):
    """Handle chat messages and return Gemini AI response."""
    try:
        body = json.loads(request.body)
        message = body.get('message', '').strip()
        history = body.get('history', [])  # [{role, text}, ...]

        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            return JsonResponse({'error': 'AI service not configured'}, status=503)

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name='gemini-3.6-flash',
            system_instruction=SYSTEM_PROMPT,
        )

        # Build conversation history for context
        gemini_history = []
        for turn in history[-10:]:  # last 10 turns to stay within token limits
            role = 'user' if turn.get('role') == 'user' else 'model'
            gemini_history.append({'role': role, 'parts': [turn.get('text', '')]})

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(message)
        reply = response.text.strip()

        return JsonResponse({'reply': reply})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Something went wrong. Please try again.'}, status=500)
