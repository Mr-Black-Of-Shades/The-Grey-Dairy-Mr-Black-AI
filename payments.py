from fastapi import APIRouter, Request, Header, HTTPException
import razorpay

from config import RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET
from db import get_cursor
from episode_service import unlock_episode


router = APIRouter()


@router.post("/payment/webhook")
async def payment_webhook(request: Request, x_razorpay_signature: str = Header(None)):

    body = await request.body()

    # ================= VERIFY SIGNATURE =================
    try:
        razorpay_client = razorpay.Client(auth=("dummy", RAZORPAY_KEY_SECRET))

        razorpay_client.utility.verify_webhook_signature(
            body,
            x_razorpay_signature,
            RAZORPAY_WEBHOOK_SECRET
        )

    except Exception as e:
        print("Webhook signature failed:", e)
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()
    event = payload.get("event")

    if event != "payment.captured":
        return {"status": "ignored"}

    payment_data = payload["payload"]["payment"]["entity"]

    razorpay_payment_id = payment_data["id"]
    razorpay_order_id = payment_data["order_id"]
    amount = payment_data["amount"] // 100

    cur = get_cursor()

    # ================= FIND PAYMENT =================
    cur.execute(
        "SELECT * FROM payments WHERE razorpay_order_id = %s",
        (razorpay_order_id,)
    )
    payment = cur.fetchone()

    if not payment:
        return {"status": "not_found"}

    user_id = payment["user_id"]
    episode_id = payment["episode_id"]
    character_id = payment["character_id"]

    # ================= CALCULATE EARNINGS =================
    cur.execute(
        "SELECT revenue_share_percent FROM characters WHERE id = %s",
        (character_id,)
    )
    char = cur.fetchone()

    share_percent = char["revenue_share_percent"] if char else 40

    character_earning = int(amount * share_percent / 100)
    platform_earning = amount - character_earning

    # ================= UPDATE PAYMENT =================
    cur.execute(
        """
        UPDATE payments
        SET 
            status = 'success',
            razorpay_payment_id = %s,
            character_earning = %s,
            platform_earning = %s
        WHERE razorpay_order_id = %s
        """,
        (
            razorpay_payment_id,
            character_earning,
            platform_earning,
            razorpay_order_id
        )
    )

    # ================= UNLOCK =================
    unlock_episode(user_id, episode_id)

    # ================= UPDATE USER =================
    cur.execute(
        """
        UPDATE users
        SET total_spent = total_spent + %s
        WHERE id = %s
        """,
        (amount, user_id)
    )

    print(f"Payment success → user {user_id}, episode {episode_id}")

    return {"status": "success"}
