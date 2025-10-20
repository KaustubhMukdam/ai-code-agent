"""
Streamlit Frontend for AI Assignment Code Pipeline
Beautiful UI that connects to your FastAPI backend
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime
import pandas as pd

# Configure page
st.set_page_config(
    page_title="AI Assignment Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

def api_call(endpoint, method="GET", data=None, files=None, auth=True):
    """Make API calls to backend"""
    headers = {}
    if auth and st.session_state.token:
        headers['Authorization'] = f"Bearer {st.session_state.token}"
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files, data=data)
            else:
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, json=data)
        else:
            response = requests.get(url, headers=headers)
        
        return response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def login_page():
    """Login/Register page"""
    st.markdown("""
    <div style='text-align: center'>
        <h1>🤖 AI Assignment Generator</h1>
        <p style='font-size: 18px; color: #666;'>Transform your assignments into professional documents</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        st.subheader("Login to your account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                # Login API call
                response = requests.post(
                    f"{API_BASE_URL}/token",
                    data={"username": username, "password": password}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data['access_token']
                    
                    # Get user info
                    user_info = api_call("/me")
                    if 'error' not in user_info:
                        st.session_state.user = user_info
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("Failed to get user info")
                else:
                    st.error("❌ Invalid username or password")
    
    with tab2:
        st.subheader("Create a new account")
        with st.form("register_form"):
            reg_username = st.text_input("Choose Username")
            reg_email = st.text_input("Email Address")
            reg_password = st.text_input("Choose Password", type="password")
            reg_confirm = st.text_input("Confirm Password", type="password")
            submit_reg = st.form_submit_button("Register", use_container_width=True)
            
            if submit_reg:
                if reg_password != reg_confirm:
                    st.error("Passwords don't match!")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    result = api_call("/register", "POST", {
                        "username": reg_username,
                        "email": reg_email,
                        "password": reg_password
                    }, auth=False)
                    
                    if 'error' not in result:
                        st.success("✅ Account created! Please login.")
                    else:
                        st.error(f"❌ Registration failed: {result['error']}")

def main_dashboard():
    """Main application dashboard"""
    # Sidebar
    with st.sidebar:
        # Fetch fresh user data
        user_data = api_call("/me")
        
        if 'error' not in user_data:
            # Update session state with fresh data
            st.session_state.user = user_data
            
            username = user_data.get('username', 'User')
            total_jobs = user_data.get('total_jobs', 0)
            email = user_data.get('email', '')
            created_at = user_data.get('created_at', '')
            subscription_tier = user_data.get('subscription_tier', 'free')
            jobs_this_month = user_data.get('total_jobs_this_month', 0)
            monthly_limit = user_data.get('monthly_job_limit', 5)
            
            st.markdown(f"""
            ### 👋 Welcome, {username}!
            
            **Account Info:**
            - 📊 Total Jobs: **{total_jobs}**
            - 📅 This Month: **{jobs_this_month}/{monthly_limit}**
            - 🎯 Tier: **{subscription_tier.title()}**
            - 📧 {email}
            - 📆 Member since: {str(created_at)[:10] if created_at else 'N/A'}
            """)
            
            # Show upgrade button for free users
            if subscription_tier == 'free' and jobs_this_month >= monthly_limit - 2:
                st.warning(f"⚠️ {monthly_limit - jobs_this_month} jobs remaining!")
                if st.button("⬆️ Upgrade Plan", use_container_width=True):
                    st.switch_page("pages/upgrade.py")  # Or handle upgrade flow
        else:
            st.error("Could not load user data")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

    
    # Main content
    st.title("🤖 AI Assignment Generator")
    
    tab1, tab2, tab3 = st.tabs(["📁 Submit Assignment", "📊 My Jobs", "📈 Analytics"])
    
    with tab1:
        st.subheader("Upload Assignment File")
        st.info("Upload a .txt file with your assignment questions. The AI will generate code and create a professional document.")
        
        uploaded_file = st.file_uploader(
            "Choose a .txt file",
            type=['txt'],
            help="Upload your assignment questions in a text file"
        )
        
        if uploaded_file:
            st.text_area("File Contents Preview:", uploaded_file.getvalue().decode(), height=200)
            
            if st.button("🚀 Generate Assignment", use_container_width=True):
                with st.spinner("Uploading and processing..."):
                    files = {'file': uploaded_file.getvalue()}
                    result = api_call("/submit-assignment", "POST", files={'file': uploaded_file})
                    
                    if 'error' not in result:
                        st.success(f"✅ Assignment submitted! Job ID: {result['job_id']}")
                        st.info("Check the 'My Jobs' tab to track progress")
                    else:
                        st.error(f"❌ Upload failed: {result['error']}")
    
    with tab2:
        st.subheader("📊 My Jobs")
        
        # Get jobs
        jobs = api_call("/my-jobs")
        
        if 'error' not in jobs and jobs:
            df = pd.DataFrame(jobs)
            
            # Format dataframe
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            df['Status'] = df['status'].str.title()
            
            # Display jobs
            for idx, job in df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        status_color = "🟢" if job['status'] == 'done' else "🟡" if job['status'] == 'processing' else "🔴"
                        st.write(f"{status_color} **Job {job['job_id'][:8]}**")
                        st.caption(f"Created: {job['created_at']}")
                    
                    with col2:
                        st.metric("Status", job['Status'])
                    
                    with col3:
                        if job['status'] == 'done':
                            if st.button(f"📥 Download", key=f"download_{job['job_id']}"):
                                # Download file
                                response = requests.get(
                                    f"{API_BASE_URL}/download/{job['job_id']}",
                                    headers={'Authorization': f"Bearer {st.session_state.token}"}
                                )
                                if response.status_code == 200:
                                    st.download_button(
                                        label="💾 Save Document",
                                        data=response.content,
                                        file_name=f"assignment_{job['job_id'][:8]}.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    )
                    
                    with col4:
                        if st.button(f"🔄 Refresh", key=f"refresh_{job['job_id']}"):
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No jobs yet. Upload an assignment to get started!")
    
    with tab3:
        st.subheader("📈 Your Analytics")
        
        # Get analytics
        analytics = api_call("/analytics/usage")
        
        if 'error' not in analytics:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Jobs", analytics['total_jobs'])
            
            with col2:
                st.metric("Success Rate", f"{analytics['success_rate']}%")
            
            with col3:
                st.metric("Tokens Used", analytics['total_tokens_used'])
            
            with col4:
                st.metric("This Month", f"{analytics['jobs_this_month']}/{analytics['monthly_limit']}")
            
            # Simple chart
            if analytics['total_jobs'] > 0:
                chart_data = pd.DataFrame({
                    'Status': ['Successful', 'Failed'],
                    'Count': [analytics['successful_jobs'], analytics['failed_jobs']]
                })
                
                st.bar_chart(chart_data.set_index('Status'))

def main():
    """Main app entry point"""
    # Custom CSS
    st.markdown("""
    <style>
        .stButton > button {
            width: 100%;
        }
        .metric-container {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Route based on authentication
    if st.session_state.token:
        main_dashboard()
    else:
        login_page()

if __name__ == "__main__":
    main()
