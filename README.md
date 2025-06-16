<h1 align="center">📄 AI Document Query System – Smart PDF Chat with RAG + OpenAI</h1>

<p align="center">
  Upload PDFs. Ask questions. Get answers instantly using cutting-edge AI.
</p>

<p align="center">
  <a href="https://www.linkedin.com/posts/your-demo-link"><img src="https://img.shields.io/badge/Demo-Watch%20Now-blue?style=for-the-badge&logo=linkedin" alt="Demo Video"/></a>
</p>

---

## 📸 Preview

<p align="center">
  <img src="Screenshot 2025-06-16 210108.png" width="700" alt="AI PDF Chat Preview" />
  <br/>
  <i>*Beautiful UI with dark mode, floating upload button, and chat interface*</i>
</p>

---

## 🔥 Features

- 📤 Upload and store multiple PDF documents
- 🤖 Ask questions in chat — powered by Retrieval-Augmented Generation (RAG)
- 🔐 Secure login/registration system with role-based access (admin & user)
- 💡 Dark mode UI with glassmorphism and animated interactions
- 🧠 OpenAI/GPT-powered answer generation from indexed content
- ⚙️ Admin panel to view and manage uploaded documents
- 🧪 Fully testable API and login flow with `test_auth.py`

---

## 🛠️ Tech Stack

| Layer      | Tech                                    |
|------------|------------------------------------------|
| Frontend   | React.js + Context API + Custom CSS      |
| Backend    | FastAPI + Python                         |
| Auth       | JWT-based login/registration             |
| Storage    | MongoDB for metadata, local/Cloudinary for docs |
| AI Engine  | RAG (Vector Search + OpenAI Completion)  |

---

## 🚀 Setup Instructions

### Prerequisites
- Node.js ≥ 14
- Python ≥ 3.8
- MongoDB URI
- OpenAI API Key

### Install & Run

```bash
# Backend setup
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend setup
cd ../frontend
npm install
npm start
