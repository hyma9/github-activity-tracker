# 🚀 GitHub Activity Tracker

A simple web dashboard that displays your GitHub activity, repositories, and productivity score.

## ✨ Features

- 📊 View your GitHub profile stats (repos, followers, following)
- 📁 List all your repositories with stars and languages
- 🎯 Calculate productivity score based on your activity
- 🔒 Secure GitHub token authentication

## 🛠️ Installation

1. **Clone or download this project**

2. **Install Python packages:**
```bash
pip install -r requirements.txt
```

3. **Get your GitHub Personal Access Token:**
   - Go to GitHub.com → Settings → Developer settings
   - Click "Personal access tokens" → "Tokens (classic)"
   - Click "Generate new token (classic)"
   - Select scopes: `repo` and `user`
   - Copy the token (starts with `ghp_`)

4. **Run the app:**
```bash
streamlit run app.py
```

5. **Open browser at:** http://localhost:8501

## 📝 How to Use

1. Enter your GitHub Personal Access Token in the sidebar
2. Click "Connect to GitHub"
3. View your dashboard with stats and repositories
4. See your productivity score!

## 🔒 Privacy

- Your token is only used to fetch data from GitHub API
- No data is stored anywhere
- Token stays in your browser session only

## 📊 Productivity Score

Score = (Number of Repos × 10) + (Total Stars ÷ 10)

Max score: 100

## 🐛 Troubleshooting

**"Invalid token" error:**
- Make sure you copied the full token
- Check that you selected `repo` and `user` scopes

**"API rate limit" error:**
- Wait an hour and try again
- GitHub limits: 5,000 requests/hour

## 📦 Tech Stack

- Python 3.x
- Streamlit (web framework)
- GitHub REST API

## 📄 License

MIT License - Free to use and modify!