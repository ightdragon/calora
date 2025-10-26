# 🥗 Calora — AI-Powered Calorie Tracker

**Calora** is a voice- and text-based calorie tracking app built with Flask, Auth0 authentication, SQLite storage, and Gemini AI for meal macro estimation.  
Users can log meals conversationally, view daily totals vs. TDEE, and update body metrics dynamically.

---

## 🚀 Features

- 🔐 **Auth0 Login** — secure authentication and session management  
- 🧠 **Gemini AI** — analyzes user-input meals to estimate calories, protein, carbs, and fat  
- 🗄️ **SQLite Database** — persistent user + meal logs  
- ⚙️ **TDEE Calculator** — gender-, height-, weight-, age-, and activity-based  
- ✏️ **Update Metrics** — easily update height, weight, age, activity, and gender  
- 🧾 **Meal History & Delete** — view, delete, and auto-refresh meal logs with recalculated totals  
- 🎨 **Modern UI** — white-orange theme, responsive layout  

---

## 🧩 Tech Stack

| Component | Technology |
|------------|-------------|
| Backend | Flask (Python) |
| Frontend | HTML, CSS, JS |
| Authentication | Auth0 |
| Database | SQLite |
| AI Integration | Google Gemini API |
| Voice Integration (optional) | ElevenLabs Conversational API |

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/calora.git
cd calora
