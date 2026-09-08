import streamlit as st
import pandas as pd
from datetime import datetime, date
import requests
import json

# Page Configuration
st.set_page_config(page_title="ANNAPURNA VEGETABLE SHOP", page_icon="🥦", layout="centered")

# --- CUSTOM CSS FOR SHOP BRANDING ---
st.markdown("""
<style>
    .stApp, p, label, .stMarkdown, .stSelectbox, div[data-baseweb="select"] {
        color: #222222 !important;
    }
    .shop-header {
        background: linear-gradient(135deg, #FF9800, #F57C00);
        color: white !important; padding: 25px; border-radius: 15px;
        text-align: center; margin-bottom: 25px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    }
    .shop-header h1 { color: white !important; font-size: 28px !important; font-weight: bold !important; margin: 0; }
    .shop-header p { color: #FFF3E0 !important; font-size: 16px !important; margin: 5px 0 0 0; }
    button[data-baseweb="tab"] p {
        color: #111111 !important;
        font-weight: bold !important;
        font-size: 15px !important;
    }
    button[aria-selected="true"] p {
        color: #E65100 !important;
        border-bottom: 2px solid #E65100;
    }
</style>
""", unsafe_allow_html=True)

# 🟢 APNI GOOGLE WEB APP KI LINK YAHAN PASTE KAREIN
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxbbUBdxj__qToZfF33nT2E3E464K9i3v6S9vDSaxLx4ll8nwNrY8gDaDQqN2sfJbQ2/exec"

# Shop Main Banner on Top
st.markdown('<div class="shop-header"><h1>🚩 ANNAPURNA VEGETABLE SHOP</h1><p>Mess Supply Demand & Billing System</p></div>', unsafe_allow_html=True)

# --- LOGIN CREDENTIALS ---
USER_CREDENTIALS = {
    "admin": "admin123",
    "hq": "hq123", "rtt": "rtt123", "ffc": "ffc123", 
    "fc": "fc123", "so_s": "so123", "go_s": "go123", "veg_shop": "veg123"
}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'mandi_rates' not in st.session_state:
    st.session_state.mandi_rates = {}

# Google Script API se live database load karna
try:
    response = requests.get(SCRIPT_URL, timeout=5)
    api_data = response.json()
    available_items = api_data.get("items", ["Aloo", "Tamatar", "Pyaj"])
    raw_demands = api_data.get("demands", [])
    if raw_demands:
        df = pd.DataFrame(raw_demands)
    else:
        df = pd.DataFrame(columns=["Date", "Mess", "Item", "Qty", "Rate", "Total"])
except Exception as e:
    available_items = ["Aloo", "Tamatar", "Pyaj"]
    df = pd.DataFrame(columns=["Date", "Mess", "Item", "Qty", "Rate", "Total"])

# Session rates ko sync karna
for item in available_items:
    if item not in st.session_state.mandi_rates:
        st.session_state.mandi_rates[item] = 0.0

# ==========================================
# 🔐 SCREEN 1: LOGIN SYSTEM
# ==========================================
if not st.session_state.logged_in:
    st.subheader("🔒 Login Karein")
    user_input = st.text_input("Username:").strip().lower()
    pass_input = st.text_input("Password:", type="password")
    login_btn = st.button("Login ✅")
    
    if login_btn:
        if user_input in USER_CREDENTIALS and USER_CREDENTIALS[user_input] == pass_input:
            st.session_state.logged_in = True
            st.session_state.username = user_input
            st.rerun()
        else:
            st.error("❌ Galat Username ya Password!")

# ==========================================
# 🔓 SCREEN 2: MAIN APP
# ==========================================
else:
    name_mapping = {
        "hq": "HQ", "rtt": "RTT", "ffc": "FFC", "fc": "FC", 
        "so_s": "SO'S", "go_s": "GO'S", "veg_shop": "VEG SHOP"
    }
    
    display_name = name_mapping.get(st.session_state.username, "ADMIN")
    st.sidebar.write(f"👤 Logged in as: **{display_name}**")
    
    if st.sidebar.button("Logout 🚪"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # ---- 🟢 MESS MANAGER LOGGED IN ----
    if st.session_state.username != "admin":
        st.subheader("📋 New Demand Form")
        current_mess = name_mapping[st.session_state.username]
        st.info(f"Aap {current_mess} ke liye demand daal rahe hain.")
        
        with st.form("demand_form", clear_on_submit=True):
            item = st.selectbox("Select Sabji / Fruit Name:", available_items)
            qty = st.number_input("Quantity (Kg / Dozen):", min_value=1.0, step=1.0)
            submit = st.form_submit_button("Submit Demand 🚀")
            
            if submit:
                payload = {
                    "action": "submit_demand",
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Mess": current_mess,
                    "Item": item,
                    "Qty": qty,
                    "Rate": 0,
                    "Total": 0
                }
                try:
                    res = requests.post(SCRIPT_URL, data=json.dumps(payload))
                    if res.status_code == 200:
                        st.success(f"✅ Success: {item} ki {qty} Qty demand record ho gayi!")
                        st.balloons()
                    else:
                        st.error(f"⚠️ Server Error! Status Code: {res.status_code}")
                except Exception as e:
                    st.error(f"❌ Connection Error: {str(e)}")
                
    # ---- 📊 ADMIN (OWNER) LOGGED IN ----
    else:
        st.markdown("### 📅 Select Working Date")
        selected_date = st.date_input("Filter Data By Date:", value=date.today())
        formatted_selected_date = selected_date.strftime("%Y-%m-%d")
        
        # ISO Timestamp (UTC) क्लीनर
        if not df.empty and "Date" in df.columns:
            def clean_date_string(date_val):
                try:
                    dt_str = str(date_val).strip()
                    if "T" in dt_str:
                        return dt_str.split("T")[0]
                    elif " " in dt_str:
                        return dt_str.split(" ")[0]
                    return dt_str
                except:
                    return str(date_val)[:10]
            df["Date_Clean"] = df["Date"].apply(clean_date_string)
            filtered_df = df[df["Date_Clean"] == formatted_selected_date].reset_index(drop=True)
        else:
            filtered_df = df.copy()

        # हेल्प बॉक्स अगर डेटा खाली है
        if filtered_df.empty and not df.empty and "Date" in df.columns:
            st.info(f"💡 यदि आज की डिमांड नहीं दिख रही है, तो कैलेंडर में एक दिन पीछे की तारीख चुनकर देखें।")

        st.info(f"📅 Abhi data sirf date: **{formatted_selected_date}** ka dikhai de raha hai.")
        st.markdown("---")

        tab1, tab2, tab3, tab4 = st.tabs(["🛒 Mandi Packing List", "➕ Add New Sabji/Fruit", "💰 Today's Mandi Rates", "💵 Alag-Alag Mess Bills"])
        
        # TAB 1: Packing List Matrix
        with tab1:
            st.subheader("🛒 Mandi Purchase Consolidated List")
            if filtered_df.empty:
                st.info("Chuni hui date ke liye abhi tak koi demand nahi mili hai.")
            else:
                filtered_df["Qty"] = pd.to_numeric(filtered_df["Qty"], errors='coerce').fillna(0)
                try:
                    matrix_df = filtered_df.pivot_table(index='Item', columns='Mess', values='Qty', aggfunc='sum', fill_value=0)
                    matrix_df['Total Qty'] = matrix_df.sum(axis=1)
                    matrix_df = matrix_df.reset_index()
                    matrix_df.columns.name = None
                    matrix_df = matrix_df.rename(columns={'Item': 'Item Name'})
                    matrix_df.index = matrix_df.index + 1
                    matrix_df.index.name = "Sl No"
                    matrix_df = matrix_df.reset_index()
                    
                    st.write(f"📊 **Mandi Packing Matrix ({formatted_selected_date}):**")
                    mandi_csv_data = matrix_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 DOWNLOAD MANDI PACKING LIST (CSV)",
                        data=mandi_csv_data,
                        file_name=f"Mandi_Packing_List_{formatted_selected_date}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    st.dataframe(matrix_df)
                except Exception as ex:
                    st.dataframe(filtered_df[["Date", "Mess", "Item", "Qty"]])

        # TAB 2: Nayi Sabji Add
        with tab2:
            st.subheader("➕ Nayi Sabji ya Fruit Ka Name Jodein")
            with st.form("add_item_form", clear_on_submit=True):
                new_item_name = st.text_input("Enter New Item Name:").strip()
                add_submit = st.form_submit_button("Add Item to Database ➕")
                if add_submit and new_item_name:
                    payload = {"action": "add_item", "item_name": new_item_name}
                    try:
                        res = requests.post(SCRIPT_URL, data=json.dumps(payload))
                        if res.status_code == 200:
                            st.success(f"✅ Success: '{new_item_name}' jodh diya gaya hai!")
                            st.rerun()
                        else:
                            st.error("⚠️ Server Error!")
                    except Exception as e:
                        st.error(f"❌ Connection Error: {str(e)}")

        # TAB 3: Today's Mandi Rates Form (100% Error Free & Fixed Syntax)
        with tab3:
            st.subheader("💰 Aaj Ke Mandi Rates Set Karein")
            with st.form("rates_form"):
                updated_rates = {}
                for item in available_items:
                    current_rate_val = 0.0
                    if not filtered_df.empty and "Item" in filtered_df.columns:
                        match = filtered_df[filtered_df["Item"] == item]
                        if not match.empty and "Rate" in match.columns:
                            try:
