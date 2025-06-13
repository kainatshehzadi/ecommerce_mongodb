from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()


EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")


def send_order_email_to_admin(
    customer_email: str,
    order_id: str,
    customer_name: str,
    items,
    total_price: float
):
    try:
        # Compose subject and body
        subject = f"New Order from {customer_name}"
        
        item_lines = "\n".join([
            f"{item['quantity']} x {item['product_id']}" for item in items
        ])
        
        body = (
            f"New Order Details:\n\n"
            f"Customer Name: {customer_name}\n"
            f"Customer Email: {customer_email}\n"
            f"Order ID: {order_id}\n"
            f"Items:\n{item_lines}\n\n"
            f"Total: ${total_price:.2f}"
        )

        # Setup email message
        message = MIMEMultipart()
        message["From"] = EMAIL_SENDER
        message["To"] = ADMIN_EMAIL
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, ADMIN_EMAIL, message.as_string())
        
        print("Email sent successfully!")

    except Exception as e:
        print(f"[Email Error] Failed to notify admin: {e}")


        '''Connect and send
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, ADMIN_EMAIL, message.as_string())
            print(" Email sent successfully!")'''

    