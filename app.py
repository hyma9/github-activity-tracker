import streamlit as st
import requests
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="GitHub Activity Tracker",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #0366d6;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #0256c7;
    }
    .metric-card {
        background-color: #f6f8fa;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e1e4e8;
    }
    .repo-card {
        background-color: white;
        padding: 1rem;
        border-radius: 6px;
        border: 1px solid #e1e4e8;
        margin-bottom: 1rem;
    }
    .score-excellent {
        color: #28a745;
        font-weight: bold;
    }
    .score-good {
        color: #0366d6;
        font-weight: bold;
    }
    .score-average {
        color: #f9826c;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# GitHub API functions with error handling
def verify_token(token):
    """Verify if the GitHub token is valid"""
    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False

def get_user_data(token):
    """Fetch user profile data from GitHub"""
    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("Invalid token. Please check your GitHub Personal Access Token.")
            return None
        elif response.status_code == 403:
            st.error("API rate limit exceeded. Please try again later.")
            return None
        else:
            st.error(f"Error fetching user data: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def get_user_repos(token, username):
    """Fetch user repositories from GitHub"""
    try:
        headers = {"Authorization": f"token {token}"}
        repos = []
        page = 1
        
        while True:
            response = requests.get(
                f"https://api.github.com/users/{username}/repos",
                headers=headers,
                params={"per_page": 100, "page": page},
                timeout=10
            )
            
            if response.status_code != 200:
                break
                
            data = response.json()
            if not data:
                break
                
            repos.extend(data)
            page += 1
            
            # Limit to 500 repos to avoid long wait times
            if len(repos) >= 500:
                break
        
        return repos
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching repositories: {str(e)}")
        return []

def calculate_productivity_score(repos_count, total_stars):
    """Calculate productivity score based on repos and stars"""
    # Score formula: (repos * 10) + (total_stars / 10)
    # Max score capped at 100
    score = (repos_count * 10) + (total_stars / 10)
    return min(score, 100)

def get_score_message(score):
    """Get motivational message based on score"""
    if score >= 80:
        return "🌟 Excellent! You're a coding superstar!", "score-excellent"
    elif score >= 50:
        return "👍 Great work! Keep building!", "score-good"
    elif score >= 20:
        return "📈 Good start! Keep pushing!", "score-average"
    else:
        return "🚀 Just getting started! Build more projects!", "score-average"

# Sidebar for token input
st.sidebar.title("🔐 GitHub Authentication")
st.sidebar.markdown("Enter your GitHub Personal Access Token to get started.")

# Token input
github_token = st.sidebar.text_input(
    "GitHub Token",
    type="password",
    help="Generate token at: github.com/settings/tokens"
)

# Instructions
with st.sidebar.expander("📝 How to get a token?"):
    st.markdown("""
    1. Go to [GitHub Settings](https://github.com/settings/tokens)
    2. Click "Generate new token (classic)"
    3. Select scopes: `repo` and `user`
    4. Click "Generate token"
    5. Copy and paste here
    """)

# Connect button
connect_clicked = st.sidebar.button("🔗 Connect to GitHub")

# Main app
st.title("📊 GitHub Activity Tracker")
st.markdown("Track your GitHub activity and productivity score!")

# Check if token is provided and valid
if github_token and connect_clicked:
    with st.spinner("Verifying token..."):
        if verify_token(github_token):
            st.sidebar.success("✅ Connected to GitHub!")
            
            # Fetch user data
            with st.spinner("Loading your data..."):
                user_data = get_user_data(github_token)
                
                if user_data:
                    # Display user profile
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        if user_data.get('avatar_url'):
                            st.image(user_data['avatar_url'], width=150)
                    
                    with col2:
                        st.markdown(f"## {user_data.get('name', 'N/A')}")
                        st.markdown(f"**@{user_data.get('login', 'N/A')}**")
                        if user_data.get('bio'):
                            st.markdown(f"*{user_data['bio']}*")
                        if user_data.get('blog'):
                            st.markdown(f"🌐 [{user_data['blog']}]({user_data['blog']})")
                    
                    st.markdown("---")
                    
                    # Fetch repositories
                    with st.spinner("Fetching repositories..."):
                        repos = get_user_repos(github_token, user_data['login'])
                    
                    # Calculate stats
                    repos_count = len(repos)
                    total_stars = sum(repo.get('stargazers_count', 0) for repo in repos)
                    total_forks = sum(repo.get('forks_count', 0) for repo in repos)
                    
                    # Display stats
                    st.subheader("📈 Your Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📁 Repositories", repos_count)
                    with col2:
                        st.metric("⭐ Total Stars", total_stars)
                    with col3:
                        st.metric("👥 Followers", user_data.get('followers', 0))
                    with col4:
                        st.metric("👤 Following", user_data.get('following', 0))
                    
                    st.markdown("---")
                    
                    # Productivity Score
                    st.subheader("🎯 Productivity Score")
                    score = calculate_productivity_score(repos_count, total_stars)
                    message, css_class = get_score_message(score)
                    
                    col1, col2 = st.columns([2, 3])
                    
                    with col1:
                        st.markdown(f"### Your Score: {score:.1f} / 100")
                        st.progress(score / 100)
                        st.markdown(f'<p class="{css_class}">{message}</p>', unsafe_allow_html=True)
                    
                    with col2:
                        st.info(f"""
                        **Score Calculation:**
                        - Repositories: {repos_count} × 10 = {repos_count * 10}
                        - Stars: {total_stars} ÷ 10 = {total_stars / 10:.1f}
                        - **Total: {score:.1f}** (capped at 100)
                        """)
                    
                    st.markdown("---")
                    
                    # Repositories list
                    st.subheader("📚 Your Repositories")
                    
                    # Filter options
                    col1, col2 = st.columns(2)
                    with col1:
                        show_count = st.selectbox("Show repositories:", [10, 25, 50, "All"], index=0)
                    with col2:
                        sort_by = st.selectbox("Sort by:", ["Stars", "Name", "Updated"], index=0)
                    
                    # Sort repos
                    if sort_by == "Stars":
                        sorted_repos = sorted(repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)
                    elif sort_by == "Name":
                        sorted_repos = sorted(repos, key=lambda x: x.get('name', '').lower())
                    else:  # Updated
                        sorted_repos = sorted(repos, key=lambda x: x.get('updated_at', ''), reverse=True)
                    
                    # Limit repos
                    if show_count != "All":
                        sorted_repos = sorted_repos[:show_count]
                    
                    # Display repos
                    for repo in sorted_repos:
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.markdown(f"### [{repo['name']}]({repo['html_url']})")
                                if repo.get('description'):
                                    st.markdown(repo['description'])
                            
                            with col2:
                                st.markdown(f"⭐ {repo.get('stargazers_count', 0)}")
                                if repo.get('language'):
                                    st.markdown(f"💻 {repo['language']}")
                            
                            with col3:
                                st.markdown(f"🍴 {repo.get('forks_count', 0)}")
                                if repo.get('updated_at'):
                                    updated = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
                                    st.markdown(f"📅 {updated.strftime('%Y-%m-%d')}")
                            
                            st.markdown("---")
                    
                    # Summary
                    st.success(f"✅ Showing {len(sorted_repos)} of {repos_count} repositories")
        else:
            st.sidebar.error("❌ Invalid token. Please try again.")
elif not github_token:
    # Welcome screen
    st.info("👈 Enter your GitHub token in the sidebar to get started!")
    
    st.markdown("### 🚀 Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📊 Stats Dashboard")
        st.markdown("View your repos, stars, followers at a glance")
    
    with col2:
        st.markdown("#### 📁 Repository List")
        st.markdown("Browse all your repositories with details")
    
    with col3:
        st.markdown("#### 🎯 Productivity Score")
        st.markdown("Get a score based on your activity")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #586069;'>"
    "Built with ❤️ using Streamlit | Data from GitHub API"
    "</div>",
    unsafe_allow_html=True
)