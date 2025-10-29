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

API_BASE_URL = "http://localhost:8000"  # Update for production

# Session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

def api_call(endpoint, method="GET", data=None, files=None, auth=True):
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
    st.markdown("## Login to your account")
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
        if submit:
            with st.spinner("Logging in..."):
                response = requests.post(
                    f"{API_BASE_URL}/token",
                    data={"username": username, "password": password}
                )
            if response.status_code == 200:
                data = response.json()
                st.session_state.token = data['access_token']
                user_info = api_call("/me")
                if 'error' not in user_info:
                    st.session_state.user = user_info
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("Failed to fetch user profile. Contact admin.")
            else:
                st.error("❌ Invalid username or password")
    with tab2:
        with st.form("register_form"):
            reg_username = st.text_input("Choose Username")
            reg_email = st.text_input("Email Address")
            reg_password = st.text_input("Choose Password", type="password", help="Min 6 chars, include A-Z, a-z, 0-9")
            reg_confirm = st.text_input("Confirm Password", type="password")
            submit_reg = st.form_submit_button("Register", use_container_width=True)
        if submit_reg:
            if reg_password != reg_confirm:
                st.error("Passwords don't match!")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters")
            elif '@' not in reg_email or '.' not in reg_email:
                st.error("Invalid email address!")
            else:
                with st.spinner("Registering..."):
                    result = api_call(
                        "/register", "POST",
                        data={
                            "username": reg_username,
                            "email": reg_email,
                            "password": reg_password
                        },
                        auth=False
                    )
                if 'error' not in result:
                    st.success("✅ Account created! Please login.")
                else:
                    st.error(f"❌ Registration failed: {result['error']}")
    st.info("Forgot password? Contact support@example.com for help.")

def job_status_color(status):
    if status == 'done':
        return '🟢'
    elif status == 'processing':
        return '🟡'
    elif status == 'error':
        return '🔴'
    else:
        return '⚪'

def show_jobs(jobs):
    st.subheader("📊 My Jobs")
    for job in jobs:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown(f"{job_status_color(job['status'])} **Job {job['job_id'][:8]}**")
            st.caption(f"Created: {job['created_at']}")
        with col2:
            st.markdown(f"**Status:** {job['status'].title()}")
            st.caption(f"{job.get('language','-').title()}")
        with col3:
            if job['status'] == 'done':
                if st.button(f"📥 Download", key=f"download_{job['job_id']}"):
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
                        st.success("File download ready!")
                    else:
                        st.error("Error downloading file.")
            else:
                st.button("📥 Download", key=f"download_disabled_{job['job_id']}", disabled=True, help="Job not ready yet.")
        with col4:
            if st.button("🔄 Refresh", key=f"refresh_{job['job_id']}"):
                st.rerun()
        with st.expander("Show job details", expanded=False):
            st.markdown(f"**Job ID:** `{job['job_id']}`")
            st.markdown(f"**Created:** {job['created_at']}")
            st.markdown(f"**Language:** {job.get('language','-')}")
            st.markdown(f"**Status:** {job['status']}")
            if job.get("output"):
                st.markdown("**Output:**")
                st.code(job['output'])
            if job.get("error"):
                st.markdown("**Error:**")
                st.error(job['error'])
            if job.get("code"):
                st.markdown("**Generated code:**")
                st.code(job['code'])
        st.divider()

def assignment_upload_section():
    st.subheader("Upload Assignment File")
    st.info("Upload a .txt file with your assignment questions. The AI will generate code and create a professional document.")
    with st.form("assignment_form"):
        uploaded_file = st.file_uploader("Choose a .txt file", type=['txt'])
        if uploaded_file:
            st.info(f"**File:** {uploaded_file.name} ({uploaded_file.size/1024:.1f} KB)")
            st.text_area("File preview:", uploaded_file.getvalue().decode(), height=200)
        submit_file = st.form_submit_button("🚀 Submit Assignment")
        if submit_file and uploaded_file:
            with st.spinner("Uploading and processing..."):
                files = {'file': uploaded_file}
                result = api_call("/submit-assignment", "POST", files=files)
            if 'error' not in result:
                st.success(f"✅ Assignment submitted! Job ID: {result['job_id']}")
            else:
                st.error(f"❌ Upload failed: {result['error']}")

def analytics_dashboard():
    st.subheader("📈 Your Analytics")
    analytics = api_call("/analytics/usage")
    if 'error' not in analytics:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Jobs", analytics.get('total_jobs', 0))
        col2.metric("Success Rate", f"{analytics.get('success_rate',0)}%")
        col3.metric("Tokens Used", analytics.get('total_tokens_used', 0))
        col4.metric("This Month", f"{analytics.get('jobs_this_month', '-')}")
        if analytics.get('total_jobs', 0) > 0:
            chart_data = pd.DataFrame({
                'Status': ['Successful', 'Failed'],
                'Count': [analytics.get('successful_jobs',0), analytics.get('failed_jobs',0)]
            })
            st.bar_chart(chart_data.set_index('Status'))
    else:
        st.info("No analytics available yet.")

def profile_tab():
    st.subheader("👤 Profile / Account Info")
    user = api_call("/me")
    if user and 'error' not in user:
        st.markdown(f"**Username:** {user['username']}")
        st.markdown(f"**Email:** {user['email']}")
        st.markdown(f"**Created:** {str(user['created_at'])[:10]}")
        st.markdown(f"**Active:** {user['is_active']}")
        st.markdown(f"**Admin:** {user.get('is_admin', False)}")
    else:
        st.warning("Could not load user info.")
    st.divider()
    st.subheader("🔑 Change Password")
    with st.form("change_password_form"):
        old_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        submit_password = st.form_submit_button("Change Password")
    if submit_password:
        if new_pw != confirm_pw:
            st.error("Password mismatch.")
        elif len(new_pw) < 6:
            st.warning("Password too short.")
        else:
            payload = {"old_password": old_pw, "new_password": new_pw}
            result = api_call("/me/change-password", method="POST", data=payload)
            if result and "success" in result:
                st.success("Password changed!")
            else:
                st.error(result.get("error", "Password change failed."))

def docs_tab():
    st.subheader("📖 Documentation / Help")
    st.markdown("""
    ### Getting Started
    - **Register/Login**: Create your account if you're a new user.
    - **Submit Assignment**: Upload a `.txt` file with each question on a new line.
    - **Track Jobs**: Use the 'My Jobs' tab to see progress and download results.

    ### Assignment Format Example

    ```
    Q1. Write a function to sum numbers in Python.
    Q2. Implement a class for Rectangle in C++.
    ```

    ### Troubleshooting
    - If you forget your password, contact support.
    - If uploads fail, confirm your file format.

    ### API
    - [Swagger/OpenAPI Docs](http://localhost:8000/docs)
    """)

def admin_tab():
    st.subheader("🛡️ Admin Dashboard")
    users = api_call("/admin/users")
    if users and isinstance(users, list):
        st.markdown("**All Users:**")
        for u in users:
            st.markdown(f"- **{u['username']}** ({u['email']}) | "
                        f"Jobs: {u.get('total_jobs', '-')}"
                        f" | Active: {u.get('is_active', False)}"
                        f" | Admin: {u.get('is_admin', False)}")
            if st.session_state.user['is_admin'] and u['username'] != st.session_state.user['username']:
                toggle_btn = st.button(
                    "Deactivate" if u.get('is_active', False) else "Activate",
                    key=f"toggle_{u['id']}"
                )
                if toggle_btn:
                    resp = api_call(f"/admin/users/{u['id']}/toggle-active", method="POST")
                    st.info(resp.get("message", "Operation complete"))
                    st.rerun()
    else:
        st.warning("No user data or unauthorized.")
    jobs = api_call("/admin/jobs")
    if jobs and isinstance(jobs, list):
        st.markdown("**All Jobs:**")
        for job in jobs:
            st.markdown(f"- **Job {job['job_id'][:8]}** by User {job['user_id']} | "
                        f"Status: {job['status']} | "
                        f"Lang: {job.get('language', '-')}")
    else:
        st.warning("No job data or unauthorized.")

def main_dashboard():
    with st.sidebar:
        user_data = api_call("/me")
        if 'error' not in user_data:
            st.session_state.user = user_data
            username = user_data.get('username', 'User')
            total_jobs = user_data.get('total_jobs', 0)
            email = user_data.get('email', '')
            created_at = user_data.get('created_at', '')
            st.markdown(f"### 👋 Welcome, {username}!")
            st.markdown(f"- **Total Jobs:** {total_jobs}")
            st.markdown(f"- **Email:** {email}")
            st.markdown(f"- **Member since:** {str(created_at)[:10] if created_at else 'N/A'}")
        else:
            st.error("Could not load user data")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

    admin_tab_index = 5 if st.session_state.user.get("is_admin", False) else None

    tabs = [
        "📁 Submit Assignment",
        "📊 My Jobs",
        "📈 Analytics",
        "👤 Profile",
        "📖 Docs/Help",
    ]
    if admin_tab_index:
        tabs.append("🛡️ Admin")
    st_tabs = st.tabs(tabs)
    with st_tabs[0]:
        assignment_upload_section()
    with st_tabs[1]:
        jobs = api_call("/my-jobs")
        if jobs and isinstance(jobs, list):
            show_jobs(jobs)
        else:
            st.info("No jobs yet. Upload an assignment to get started!")
    with st_tabs[2]:
        analytics_dashboard()
    with st_tabs[3]:
        profile_tab()
    with st_tabs[4]:
        docs_tab()
    if admin_tab_index:
        with st_tabs[5]:
            admin_tab()

def main():
    if st.session_state.token:
        main_dashboard()
    else:
        login_page()

if __name__ == "__main__":
    main()
