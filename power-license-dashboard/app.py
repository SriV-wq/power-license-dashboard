import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime
import urllib.parse

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CORPORATE STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Power International Holding - License Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
    <style>
    .main-title { font-size: 28px; font-weight: bold; color: #1E3A8A; }
    .sub-title { font-size: 14px; color: #059669; font-weight: bold; }
    .stButton>button { border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SUPABASE API CONNECTION INITIALIZATION
# -----------------------------------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# -----------------------------------------------------------------------------
# 3. DATA FETCHING & DYNAMIC STATUS CALCULATION
# -----------------------------------------------------------------------------
def load_active_licenses():
    response = supabase.table("license_inventory").select("*").eq("is_active", True).execute()
    data = response.data
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    today = date.today()
    df["renewal_date_dt"] = pd.to_datetime(df["renewal_date"]).dt.date
    df["days_remaining"] = df["renewal_date_dt"].apply(lambda d: (d - today).days)
    
    def calculate_status(days):
        if days <= 30:
            return "🔴 CRITICAL"
        elif days <= 90:
            return "🟡 WARNING"
        else:
            return "🟢 HEALTHY"
            
    df["alert_status"] = df["days_remaining"].apply(calculate_status)
    df = df.sort_values(by="days_remaining", ascending=True)
    return df

def load_active_vendors():
    response = supabase.table("vendor_directory").select("*").eq("is_active", True).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

# -----------------------------------------------------------------------------
# 4. DASHBOARD HEADER
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">🛡️ Power International Holding</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">🟢 LIVE - Network & Security License Operations (Auto-Syncing with Supabase)</div>', unsafe_allow_html=True)
st.divider()

df = load_active_licenses()
df_vendors = load_active_vendors()

# -----------------------------------------------------------------------------
# 5. EXECUTIVE METRIC CARDS
# -----------------------------------------------------------------------------
if not df.empty:
    total_products = len(df)
    critical_count = len(df[df["days_remaining"] <= 30])
    warning_count = len(df[(df["days_remaining"] > 30) & (df["days_remaining"] <= 90)])
    healthy_count = len(df[df["days_remaining"] > 90])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Active Products", total_products)
    m2.metric("🔴 Critical (≤30 Days)", critical_count)
    m3.metric("🟡 Warning (31–90 Days)", warning_count)
    m4.metric("🟢 Healthy (>90 Days)", healthy_count)
    st.divider()

# -----------------------------------------------------------------------------
# 6. SIDEBAR: ADD APPLIANCES & MANAGE VENDORS
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Management Console")

# Form: Add New Appliance
with st.sidebar.expander("➕ Add Security Appliance"):
    p_name = st.text_input("Product Name (e.g. Palo Alto PA-3200)")
    v_name = st.selectbox("Vendor", df_vendors["vendor_name"].tolist() if not df_vendors.empty else ["Other"])
    p_cat = st.selectbox("Category", ["Firewall / NGFW", "Endpoint / EDR", "SIEM / Logging", "VPN / ZTNA", "PKI / SSL Certificates", "Load Balancer / ADC"])
    p_serial = st.text_input("License / Serial ID")
    v_email = st.text_input("Vendor Contact Email")
    p_renewal = st.date_input("Renewal Date", value=date.today())

    if st.button("Save Appliance to Supabase"):
        if p_name and p_serial:
            new_record = {
                "product_name": p_name,
                "vendor_name": v_name,
                "category": p_cat,
                "serial_license_id": p_serial,
                "vendor_email": v_email,
                "start_date": str(date.today()),
                "renewal_date": str(p_renewal),
                "is_active": True
            }
            supabase.table("license_inventory").insert(new_record).execute()
            st.sidebar.success(f"Successfully added {p_name}!")
            st.rerun()

# Form: Manage Vendors
with st.sidebar.expander("🏢 Manage Vendors"):
    new_v_name = st.text_input("New Vendor Name")
    new_v_email = st.text_input("Vendor Email")
    new_v_cat = st.text_input("Vendor Category", value="General")
    if st.button("Add Vendor"):
        if new_v_name and new_v_email:
            supabase.table("vendor_directory").insert({
                "vendor_name": new_v_name,
                "contact_email": new_v_email,
                "category": new_v_cat,
                "is_active": True
            }).execute()
            st.sidebar.success("Vendor Added!")
            st.rerun()

    del_v_name = st.selectbox("Deactivate Vendor", ["Select..."] + (df_vendors["vendor_name"].tolist() if not df_vendors.empty else []))
    if st.button("Deactivate Vendor"):
        if del_v_name != "Select...":
            supabase.table("vendor_directory").update({"is_active": False}).eq("vendor_name", del_v_name).execute()
            st.sidebar.success(f"Deactivated {del_v_name}")
            st.rerun()

# -----------------------------------------------------------------------------
# 7. ACTIVE LICENSE TABLE & ROW ACTIONS
# -----------------------------------------------------------------------------
st.subheader("📋 Active License Inventory")

if df.empty:
    st.info("No active licenses found in Supabase.")
else:
    for idx, row in df.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([2.5, 2, 2, 1.5, 1.5, 2.5])
        
        with c1:
            st.markdown(f"**{row['product_name']}**\n\n`{row['serial_license_id']}`")
        with c2:
            st.text(f"Vendor: {row['vendor_name']}\nCat: {row['category']}")
        with c3:
            st.text(f"Renewal Date: {row['renewal_date']}")
        with c4:
            st.markdown(f"**{row['days_remaining']} Days**")
        with c5:
            st.markdown(f"### {row['alert_status']}")
        with c6:
            col_q, col_r, col_d = st.columns(3)
            
            # ACTION 1: Request Quote
            subject = urllib.parse.quote(f"License Renewal Quote Request - {row['product_name']} - Power International Holding")
            body = urllib.parse.quote(f"Dear {row['vendor_name']} Team,\n\nPlease provide a renewal quote for:\nProduct: {row['product_name']}\nSerial ID: {row['serial_license_id']}\nExpiration Date: {row['renewal_date']}\n\nThank you,\nPower International Holding")
            mailto_url = f"mailto:{row['vendor_email']}?subject={subject}&body={body}"
            col_q.markdown(f"[✉️ Quote]({mailto_url})")

            # ACTION 2: Renew License
            if col_r.button("🔄 Renew", key=f"renew_btn_{row['id']}"):
                st.session_state[f"show_renew_{row['id']}"] = True

            # ACTION 3: Soft Delete
            if col_d.button("🗑️ Delete", key=f"del_btn_{row['id']}"):
                supabase.table("license_inventory").update({
                    "is_active": False,
                    "deactivated_at": datetime.now().isoformat(),
                    "deactivated_by": "admin@powerholding.com"
                }).eq("id", row["id"]).execute()
                st.success(f"Soft-deleted {row['product_name']}. Audit record retained in Supabase.")
                st.rerun()

        # Modal/Form for Date Extension on Renewal
        if st.session_state.get(f"show_renew_{row['id']}", False):
            with st.form(key=f"renew_form_{row['id']}"):
                new_expiration_date = st.date_input("Select New Expiration Date", value=date.today())
                if st.form_submit_button("Confirm Renewal"):
                    supabase.table("license_inventory").update({
                        "renewal_date": str(new_expiration_date),
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", row["id"]).execute()
                    st.session_state[f"show_renew_{row['id']}"] = False
                    st.success("License updated successfully!")
                    st.rerun()
        st.divider()
