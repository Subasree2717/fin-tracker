import streamlit as st
import pandas as pd
import random
from datetime import datetime
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# 1. Set background and page config
st.set_page_config(page_title=" Fin Tracker", page_icon="💸")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f4e2d8, #ba8b02);
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .main > div {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 2rem;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.85);
    }
    </style>
""", unsafe_allow_html=True)


# 2. Load and save user credentials from a JSON file
def load_users():
    try:
        with open("users.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file)

users = load_users()

# 3. Sustainability tips
eco_tips = [
    "Use reusable bags instead of plastic ones.",
    "Opt for public transport or carpooling to reduce emissions.",
    "Switch to energy-efficient appliances to save energy.",
    "Reduce food waste by planning meals ahead.",
    "Support local and eco-friendly businesses.",
    "Opt for digital receipts instead of paper ones.",
    "Conserve water by fixing leaks and using water-saving fixtures."
]

# 4. Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"

# 5. Login and Registration
if st.session_state.page == "login":
    st.title("🔐 FIN TRACKER ")
    option = st.radio("Select Action", ["Login", "Register"])

    if option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "main"
                st.success("Logged in successfully!")
                st.rerun()  # Important: rerun to show main app
            else:
                st.error("Invalid username or password.")

    elif option == "Register":
        st.subheader("Register New User")
        new_username = st.text_input("Choose a Username")
        new_password = st.text_input("Choose a Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if new_username in users:
                st.error("Username already exists. Please choose a different one.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                users[new_username] = new_password
                save_users(users)
                st.success(f"Account for {new_username} created successfully! Please log in.")
                st.session_state.page = "login"
                st.rerun()  # Redirect back to login

    st.stop()

# 6. Initialize user-specific data
@st.cache_data
def init_data():
    return pd.DataFrame(columns=["Date", "Category", "Amount", "Eco-Friendly", "Description", "User"])

if "expenses" not in st.session_state:
    st.session_state.expenses = init_data()

# 7. Main App Interface
if st.session_state.page == "main" and st.session_state.logged_in:
        # 🌗 Dark Mode Toggle
    dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=False)
    st.session_state["theme"] = "dark" if dark_mode else "light"

    # Adjust text and panel style based on toggle
    font_color = "white" if dark_mode else "black"
    panel_bg = "rgba(0, 0, 0, 0.6)" if dark_mode else "rgba(255, 255, 255, 0.85)"

    st.markdown(
        f"""
        <style>
        .main > div {{
            background-color: {panel_bg};
            padding: 2rem;
            border-radius: 10px;
            color: {font_color};
        }}
        body, .stApp {{
            color: {font_color};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title(f"💸 Welcome {st.session_state.username}!")
    menu = st.sidebar.selectbox("Menu", ["➕ Add Expense", "📊 View Summary", "📁 All Records", "🔓 Logout"])

    # Logout
    if menu == "🔓 Logout":
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.page = "login"
        st.rerun()

    # Add Expense
    if menu == "➕ Add Expense":
        st.subheader("➕ Add New Expense")
        with st.form("expense_form"):
            date = st.date_input("Date", value=datetime.today())
            category = st.selectbox("Category", ["Food", "Transport", "Utilities", "Shopping", "Health", "Other"])
            amount = st.number_input("Amount ($)", min_value=0.0, step=0.1)
            eco = st.radio("Eco-Friendly?", ["Yes", "No"], horizontal=True)
            desc = st.text_input("Description")
            submit = st.form_submit_button("Add")

        if submit:
            new = {
                "Date": date,
                "Category": category,
                "Amount": amount,
                "Eco-Friendly": eco,
                "Description": desc,
                "User": st.session_state.username
            }
            # Fix for FutureWarning
            if st.session_state.expenses.empty:
                st.session_state.expenses = pd.DataFrame([new])  # Directly assign if empty
            else:
                st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([new])], ignore_index=True)
            st.success("Expense added successfully!")
    

    # View Summary
    elif menu == "📊 View Summary":
        st.subheader("📊 Expense Summary")
        period = st.selectbox("View By", ["Weekly", "Monthly", "Yearly"])
        df = st.session_state.expenses
        user_df = df[df["User"] == st.session_state.username]

        if user_df.empty:
            st.warning("No expenses found.")
        else:
            today = datetime.today()
            if period == "Weekly":
                start_date = today - pd.Timedelta(days=7)
            elif period == "Monthly":
                start_date = today.replace(day=1)
            else:
                start_date = today.replace(month=1, day=1)

            filtered = user_df[pd.to_datetime(user_df["Date"]) >= pd.to_datetime(start_date)]
            total = filtered["Amount"].sum()
            eco_total = filtered[filtered["Eco-Friendly"] == "Yes"]["Amount"].sum()
            eco_percent = (eco_total / total * 100) if total > 0 else 0

            col1, col2 = st.columns(2)
            col1.metric("Total Spent", f"${total:.2f}")
            col2.metric("Eco-Friendly Spend", f"${eco_total:.2f} ({eco_percent:.1f}%)")
            st.progress(min(eco_percent / 100, 1.0), text="Eco-Friendly Spending Ratio")

            if eco_percent < 40:
                st.warning("⚠️ Try to spend more on eco-friendly alternatives when possible!")

            high_expense = filtered[filtered["Amount"] > 100]
            if not high_expense.empty:
                st.info("🔎 Consider reviewing these large expenses:")
                st.dataframe(high_expense[["Date", "Category", "Amount", "Description"]])
            
            # --- Chart Summary ---
            
            st.markdown("### 📈 Expense Breakdown by Category")
            category_summary = filtered.groupby("Category")["Amount"].sum().sort_values(ascending=False)
            if not category_summary.empty:
                st.bar_chart(category_summary)
            else:
                st.info("No expenses to visualize.")
            
            #expenses over time
               
            st.markdown("### 📅 Expense Trend Over Time")
            time_series = filtered.copy()
            time_series["Date"] = pd.to_datetime(time_series["Date"])
            daily_expense = time_series.groupby("Date")["Amount"].sum()
            if not daily_expense.empty:
                st.line_chart(daily_expense)
            else:
                st.info("No daily trend data available.")
    
            st.markdown("### 💡 Sustainability Tip")
            st.success(random.choice(eco_tips))

    # View All Records
    elif menu == "📁 All Records":
        st.subheader("📁 All Expense Records")
        df = st.session_state.expenses
        user_df = df[df["User"] == st.session_state.username]

        if user_df.empty:
            st.info("No expense records yet.")
        else:
            # Convert 'Date' column to datetime
            user_df["Date"] = pd.to_datetime(user_df["Date"])

            # --- Filter Sidebar ---
            with st.expander("🔍 Filter Records"):
                category_filter = st.multiselect("Filter by Category", options=user_df["Category"].unique())
                desc_keyword = st.text_input("Search in Description")
                start_date = st.date_input("Start Date", user_df["Date"].min().date())
                end_date = st.date_input("End Date", user_df["Date"].max().date())

            filtered_df = user_df[
                (user_df["Category"].isin(category_filter) if category_filter else True) &
                (user_df["Date"].dt.date >= start_date) &
                (user_df["Date"].dt.date <= end_date) &
                (user_df["Description"].str.contains(desc_keyword, case=False, na=False) if desc_keyword else True)
            ]

            st.write(f"### 📑 Showing {len(filtered_df)} filtered records")
            st.dataframe(filtered_df.style.format({"Amount": "${:.2f}"}))
            def generate_pdf(dataframe):
                buffer = BytesIO()
                pdf = canvas.Canvas(buffer, pagesize=letter)
                pdf.setFont("Helvetica", 10)
                pdf.drawString(30, 750, "Expense Records")
                pdf.drawString(30, 735, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                pdf.drawString(30, 720, "-" * 80)

                y = 700
                for i, row in dataframe.iterrows():
                    line = f"{row['Date']} | {row['Category']} | ${row['Amount']:.2f} | {row['Eco-Friendly']} | {row['Description']}"
                    pdf.drawString(30, y, line)
                    y -= 15
                    if y < 50:  # Create a new page if space runs out
                        pdf.showPage()
                        pdf.setFont("Helvetica", 10)
                        y = 750

                pdf.save()
                buffer.seek(0)
                return buffer

            pdf_buffer = generate_pdf(filtered_df)
            st.download_button(
                "Download Records as PDF",
                pdf_buffer,
                "expenses.pdf",
                "application/pdf"
            )
