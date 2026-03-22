import streamlit as st
import requests
from datetime import datetime
import base64
import os
from groq import Groq
from dotenv import load_dotenv

# Load API key safely from .env file
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Page configuration
st.set_page_config(
    page_title="GitHub Activity Tracker",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stButton>button {
        width: 100%;
        background-color: #0366d6;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton>button:hover { background-color: #0256c7; }
    .score-excellent { color: #28a745; font-weight: bold; }
    .score-good { color: #0366d6; font-weight: bold; }
    .score-average { color: #f9826c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Configure Groq client
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

# ── Initialize session state ──────────────────────
if "connected" not in st.session_state:
    st.session_state.connected = False
if "user_data" not in st.session_state:
    st.session_state.user_data = None
if "repos" not in st.session_state:
    st.session_state.repos = []
if "github_token" not in st.session_state:
    st.session_state.github_token = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "selected_repo" not in st.session_state:
    st.session_state.selected_repo = ""

def verify_token(token):
    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False

def get_user_data(token):
    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("Invalid token. Please check your GitHub Personal Access Token.")
        elif response.status_code == 403:
            st.error("API rate limit exceeded. Please try again later.")
        else:
            st.error(f"Error fetching user data: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def get_user_repos(token, username):
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
            if len(repos) >= 500:
                break
        return repos
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching repositories: {str(e)}")
        return []

def calculate_productivity_score(repos_count, total_stars):
    score = (repos_count * 10) + (total_stars / 10)
    return min(score, 100)

def get_score_message(score):
    if score >= 80:
        return "🌟 Excellent! You're a coding superstar!", "score-excellent"
    elif score >= 50:
        return "👍 Great work! Keep building!", "score-good"
    elif score >= 20:
        return "📈 Good start! Keep pushing!", "score-average"
    else:
        return "🚀 Just getting started! Build more projects!", "score-average"

def analyze_repo_with_ai(token, username, repo_name):
    try:
        headers = {"Authorization": f"token {token}"}

        response = requests.get(
            f"https://api.github.com/repos/{username}/{repo_name}/git/trees/HEAD?recursive=1",
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            return "❌ Could not fetch repository files. Make sure the repo is not empty."

        tree = response.json().get("tree", [])

        code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
                           '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb']
        code_files = [f for f in tree if any(f['path'].endswith(ext) for ext in code_extensions)]
        code_files = code_files[:5]

        if not code_files:
            return "❌ No code files found in this repository."

        all_code = ""
        for file in code_files:
            file_response = requests.get(
                f"https://api.github.com/repos/{username}/{repo_name}/contents/{file['path']}",
                headers=headers,
                timeout=10
            )
            if file_response.status_code == 200:
                content = file_response.json().get("content", "")
                try:
                    decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
                    all_code += f"\n\n### File: {file['path']}\n{decoded[:2000]}"
                except:
                    pass

        if not all_code:
            return "❌ Could not read file contents."

        prompt = f"""Analyze this GitHub repository and give specific, actionable suggestions on:
1. Code quality improvements
2. Repository structure improvements
3. Best practices that are missing

Be concise, practical, and beginner-friendly. Use bullet points.

Repository: {repo_name}

Code:
{all_code}"""

        result = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return result.choices[0].message.content

    except Exception as e:
        return f"❌ Analysis error: {str(e)}"

# ── Sidebar ───────────────────────────────────────
st.sidebar.title("🔐 GitHub Authentication")
st.sidebar.markdown("Enter your GitHub Personal Access Token to get started.")

github_token = st.sidebar.text_input(
    "GitHub Token",
    type="password",
    help="Generate token at: github.com/settings/tokens"
)

with st.sidebar.expander("📝 How to get a token?"):
    st.markdown("""
    1. Go to [GitHub Settings](https://github.com/settings/tokens)
    2. Click "Generate new token (classic)"
    3. Select scopes: `repo` and `user`
    4. Click "Generate token"
    5. Copy and paste here
    """)

connect_clicked = st.sidebar.button("🔗 Connect to GitHub")

# ── Handle Connect ────────────────────────────────
if connect_clicked and github_token:
    with st.spinner("Verifying token..."):
        if verify_token(github_token):
            st.session_state.github_token = github_token
            st.session_state.connected = True
            st.session_state.analysis_result = ""

            with st.spinner("Loading your data..."):
                st.session_state.user_data = get_user_data(github_token)

            with st.spinner("Fetching repositories..."):
                st.session_state.repos = get_user_repos(github_token, st.session_state.user_data['login'])

            st.sidebar.success("✅ Connected to GitHub!")
        else:
            st.session_state.connected = False
            st.sidebar.error("❌ Invalid token. Please try again.")

# ── Main App ──────────────────────────────────────
st.title("📊 GitHub Activity Tracker")
st.markdown("Track your GitHub activity and get AI-powered code suggestions!")

if st.session_state.connected and st.session_state.user_data:
    user_data = st.session_state.user_data
    repos = st.session_state.repos

    # Profile
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

    # Stats
    repos_count = len(repos)
    total_stars = sum(repo.get('stargazers_count', 0) for repo in repos)
    total_forks = sum(repo.get('forks_count', 0) for repo in repos)

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

    # Score
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

    # 🤖 AI Code Analysis
    st.subheader("🤖 AI Code Analysis")
    st.markdown("Select any repository and get instant AI-powered suggestions!")

    repo_names = [repo['name'] for repo in repos]
    selected_repo = st.selectbox("Select a repository to analyze:", repo_names)

    if st.button("🔍 Analyze My Code"):
        if not GROQ_API_KEY:
            st.error("❌ Groq API key not found! Please check your .env file.")
        else:
            with st.spinner("🤖 Analyzing your code... please wait..."):
                result = analyze_repo_with_ai(
                    st.session_state.github_token,
                    user_data['login'],
                    selected_repo
                )
                st.session_state.analysis_result = result
                st.session_state.selected_repo = selected_repo

    # Always show analysis result if it exists
    if st.session_state.analysis_result:
        st.markdown(f"### 📋 Analysis Results for `{st.session_state.selected_repo}`")
        st.markdown(st.session_state.analysis_result)

    st.markdown("---")

    # Repos list
    st.subheader("📚 Your Repositories")
    col1, col2 = st.columns(2)
    with col1:
        show_count = st.selectbox("Show repositories:", [10, 25, 50, "All"], index=0)
    with col2:
        sort_by = st.selectbox("Sort by:", ["Stars", "Name", "Updated"], index=0)

    if sort_by == "Stars":
        sorted_repos = sorted(repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)
    elif sort_by == "Name":
        sorted_repos = sorted(repos, key=lambda x: x.get('name', '').lower())
    else:
        sorted_repos = sorted(repos, key=lambda x: x.get('updated_at', ''), reverse=True)

    if show_count != "All":
        sorted_repos = sorted_repos[:show_count]

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

    st.success(f"✅ Showing {len(sorted_repos)} of {repos_count} repositories")

else:
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
        st.markdown("#### 🤖 AI Code Analysis")
        st.markdown("Get instant AI suggestions on your code")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #586069;'>"
    "Built with ❤️ using Streamlit | Data from GitHub API | AI by Groq"
    "</div>",
    unsafe_allow_html=True
)
