from datetime import date
import smtplib
from email.mime.text import MIMEText
from db_connection import get_connection

def send_email(receiver, subject, message):
    sender = "expiry.reminder7@gmail.com"
    password = "gchdufwsgzkszbxu"
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        email_message = f"Subject: {subject}\n\n{message}"
        server.sendmail(sender, receiver, email_message)

def has_reminder_sent(user_id, product_id, remind_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM reminders
        WHERE user_id=%s AND product_id=%s AND reminder_date=%s
    """, (user_id, product_id, remind_date))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def mark_reminder_sent(user_id, product_id, remind_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reminders (user_id, product_id, reminder_date)
        VALUES (%s, %s, %s)
    """, (user_id, product_id, remind_date))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users")
    users = cur.fetchall()
    conn.close()
    return users

def get_products_with_days_left(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, product_name, expiry_date, DATEDIFF(expiry_date, CURDATE()) AS days_left
        FROM products
        WHERE user_id=%s
    """, (user_id,))
    data = cur.fetchall()
    conn.close()
    return data

def send_expiry_reminders():
    today = date.today()
    users = get_all_users()
    for user_id, user_email in users:
        products = get_products_with_days_left(user_id)
        lines = []
        for product_id, name, exp_date, days_left in products:
            if days_left in [3, 2, 1]:
                if not has_reminder_sent(user_id, product_id, today):
                    lines.append(f"- {name} expires on {exp_date} ({days_left} days left)")
                    mark_reminder_sent(user_id, product_id, today)
        if lines:
            subject = "Expiry Reminder"
            body = "Dear user,\n\nThese products are expiring soon:\n\n" + "\n".join(lines) + "\n\nPlease check them."
            try:
                send_email(user_email, subject, body)
                print(f"Emailed {user_email} for: {lines}")
            except Exception as e:
                print(f"Failed for {user_email}: {e}")

if __name__ == "__main__":
    send_expiry_reminders()
