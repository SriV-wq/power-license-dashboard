# Power International Holding - Network & Security License Dashboard

Operational Web Dashboard for tracking Network & Security Licenses, managing vendors, renewing subscriptions, and handling soft-deletes with Supabase (PostgreSQL) and Streamlit.

## Folder Structure
```
power-license-dashboard/
├── .gitignore               # Ignores sensitive keys and cache
├── requirements.txt         # Python dependencies
├── schema.sql               # Supabase database setup & seed data
├── app.py                   # Streamlit web application
├── README.md                # Project documentation
└── .streamlit/
    └── secrets.toml         # Local secrets configuration
```

## Setup Instructions

### Step 1: Initialize Supabase Database
1. Log in to your Supabase account.
2. Go to the SQL Editor tab, paste the contents of `schema.sql`, and click Run.
3. Copy your Project URL and anon public Key from Project Settings > API.

### Step 2: Configure Secrets
Update `.streamlit/secrets.toml` locally with your Supabase keys:
```toml
SUPABASE_URL = "your-supabase-url-here"
SUPABASE_KEY = "your-supabase-key-here"
```

### Step 3: Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Step 4: Deploy to Streamlit Community Cloud
1. Push this project folder to your GitHub repository.
2. Go to Streamlit Community Cloud (share.streamlit.io).
3. Deploy the repository and add SUPABASE_URL and SUPABASE_KEY under Advanced Settings > Secrets.
