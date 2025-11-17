import streamlit as st
import datetime
import smtplib
from db_connection import get_connection

# ---------- CSS ----------
st.markdown("""
    <style>
    body {background-color: #f5f7fa; font-family: 'Arial';}
    .stButton>button {background-color: #4CAF50; color: white; border-radius: 8px; padding: 10px 20px;}
    </style>
""", unsafe_allow_html=True)

# ---------- Email Function ----------
def send_email(receiver, subject, message):
    print(receiver, subject, message)
    sender = "expiry.reminder7@gmail.com"
    password = "gchdufwsgzkszbxu"  # <-- your Gmail App Password
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)

            email_message = f"Subject: {subject}\n\n{message}"
            server.sendmail(sender, receiver, email_message)
        print(f"Email sent successfully to {receiver} with subject '{subject}'")
        return True
    except Exception as e:
        print("Email failed:", e)
        return False

# ---------- Database Functions ----------
def login(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (username, password))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def get_user_email(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def get_user(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    result = cur.fetchone()
    conn.close()
    return result

def add_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()
    conn.close()

def update_user_password(user_id, new_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password=%s WHERE id=%s", (new_password, user_id))
    conn.commit()
    conn.close()

def save_product(user_id, product, expiry_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (user_id, product_name, expiry_date) VALUES (%s, %s, %s)",
                (user_id, product, expiry_date))
    conn.commit()
    conn.close()

def get_products_with_days_left(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, product_name, expiry_date, DATEDIFF(expiry_date, CURDATE()) AS days_left
        FROM products
        WHERE user_id=%s
        ORDER BY expiry_date
    """, (user_id,))
    data = cur.fetchall()
    conn.close()
    return data

def delete_product(prod_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (prod_id,))
    conn.commit()
    conn.close()

def update_product(product_name, new_name, new_expiry):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE products SET product_name=%s, expiry_date=%s WHERE id=%s",
                (new_name, new_expiry, product_name))
    conn.commit()
    conn.close()

# ---------- Reminder Helpers ----------
def has_reminder_sent(user_id, product_name, remind_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM reminders
        WHERE user_id=%s AND product_id=%s AND reminder_date=%s
    """, (user_id, product_name, remind_date))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def mark_reminder_sent(user_id, product_name, remind_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reminders (user_id, product_id, reminder_date)
        VALUES (%s, %s, %s)
    """, (user_id, product_name, remind_date))
    conn.commit()
    conn.close()

def send_expiry_reminders(user_id, user_email):
    today = datetime.date.today()
    products = get_products_with_days_left(user_id)
    lines = []
    for pid, pname, pexp, days_left in products:
        print(f"Checking: {pname} exp:{pexp} days_left:{days_left}")  # debug
        if days_left in [3,2,1]:
            if not has_reminder_sent(user_id, pid, today):
                lines.append(f"BELL {pname} (expires {pexp}, {days_left} day{'s' if days_left>1 else ''} left)")
                mark_reminder_sent(user_id, pid, today)
        if lines:
            subject = "Product Expiry Reminder"
            body = (
                "Hello! \n\nThe following products from your account will expire soon:\n\n"
                + "\n".join(lines) +
                "\n\nPlease take necessary action.\n\nThanks for using Product Expiry App! CLOCK"
            )
            print(f"Sending reminder email to: {user_email}\nSubject: {subject}\nBody:\n{body}")  # debug
            send_email(user_email, subject, body)
            return len(lines)
    return 0

# ---------- Streamlit UI ----------
if "user_id" not in st.session_state:
    st.session_state.user_id = None

st.title("📦 Product Expiry Tracker")

if st.session_state.user_id is None:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
    with tab1:
        st.markdown("Welcome back! Please log in below 👋")
        username = st.text_input("Email (Username)", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", key="login_btn"):
            user_id = login(username, password)
            if user_id:
                st.session_state.user_id = user_id
                st.success("✅ Login Successful! 🎉")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Try again! 🚫")

    with tab2:
        st.markdown("New here? Create your account below 🆕")
        new_username = st.text_input("Email for Sign Up", key="signup_user")
        new_password = st.text_input("Password for Sign Up", type="password", key="signup_pass")
        if st.button("Sign Up", key="signup_btn"):
            if not new_username or not new_password:
                st.warning("⚠️ Please fill all fields!")
            elif get_user(new_username):
                st.error("❌ Email already registered!")
            else:
                add_user(new_username, new_password)
                st.success("👏 Registration successful! Please go to Login tab.")

else:
    user_email = get_user_email(st.session_state.user_id)

    # SIDEBAR WITH USER OPTIONS
    st.sidebar.markdown(f"👤 **User:** {user_email}")

    # Test Email in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 📧 Test Email")
    test_email = st.sidebar.text_input("Email to test", value=user_email, key="test_email_input")
    if st.sidebar.button("Send Test Email"):
        try:
            if send_email(test_email, "Test from Product Expiry App", "This is a test email! "):
                st.sidebar.success("✅ Email sent!")
            else:
                st.sidebar.error("❌ Email failed")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

    # User Edit Options in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ⚙️ Account Settings")
    new_password = st.sidebar.text_input("New Password", type="password", key="new_password_input")
    if st.sidebar.button("Update Password"):
        if new_password:
            update_user_password(st.session_state.user_id, new_password)
            st.sidebar.success("✅ Password updated!")
        else:
            st.sidebar.warning("⚠️ Enter new password")

    # Logout in Sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user_id = None
        st.rerun()

    # MAIN CONTENT AREA
    st.markdown("Track your products. Get notified before expiry! ⏰")
    st.markdown("### ➕ Add New Product")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        pname = st.text_input("Product Name 🏷️", key="new_product_name")
    with col2:
        pexp = st.date_input("Expiry Date 📅", key="new_product_date")
    with col3:
        st.write("")
        if st.button("💾 Save", key="save_product_btn"):
            if pname:
                save_product(st.session_state.user_id, pname, pexp)
                st.success("✅ Product Saved!")
                st.rerun()
            else:
                st.warning("⚠️ Name required!")

    st.markdown("### 📋 Your Products")
    products = get_products_with_days_left(st.session_state.user_id)

    if products:
        try:
            sent_count = send_expiry_reminders(st.session_state.user_id, user_email)
            if sent_count:
                st.success(f"📬 Sent {sent_count} expiry reminder email(s)!")
        except Exception as e:
            st.warning(f"⚠️ Email reminder failed: {e}")
        for pid, pname, pexp, days_left in products:
            if days_left < 0:
                status_color = "🔴"
                status_text = "Expired"
            elif days_left <= 3:
                status_color = "🟡"
                status_text = f"{days_left} days left"
            else:
                status_color = "🟢"
                status_text = f"{days_left} days left"

            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
            with col1:
                st.write(f"**{pname}**")
            with col2:
                st.write(f"📅 {pexp}")
            with col3:
                st.write(f"{status_color} {status_text}")
            with col4:
                if st.button("🗑️", key=f"del_{pid}", help=f"Delete {pname}"):
                    delete_product(pid)
                    st.success(f"Deleted {pname}")
                    st.rerun()
            with col5:
                if st.button("✏️", key=f"edit_{pid}", help=f"Edit {pname}"):
                    st.session_state[f"editing_{pid}"] = True
                    st.rerun()
            if st.session_state.get(f"editing_{pid}", False):
                with st.expander(f"✏️ Edit {pname}", expanded=True):
                    edit_col1, edit_col2, edit_col3, edit_col4 = st.columns([2, 2, 1, 1])
                    with edit_col1:
                        new_name = st.text_input("Product Name", value=pname, key=f"edit_name_{pid}")
                    with edit_col2:
                        new_expiry = st.date_input("Expiry Date", value=pexp, key=f"edit_date_{pid}")
                    with edit_col3:
                        if st.button("💾", key=f"save_edit_{pid}"):
                            update_product(pid, new_name, new_expiry)
                            st.session_state[f"editing_{pid}"] = False
                            st.success("✅ Updated!")
                            st.rerun()
                    with edit_col4:
                        if st.button("❌", key=f"cancel_edit_{pid}"):
                            st.session_state[f"editing_{pid}"] = False
                            st.rerun()
            st.markdown("---")
    else:
        st.info("📝 No products found. Add your first product above!")
    st.markdown("🚩 **Legend:** 🟢 Fresh • 🟡 Expiring Soon • 🔴 Expired")
