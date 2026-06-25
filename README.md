# 💰 Smart Expense Tracker

A full-featured personal expense tracking web app built with Django. Track your spending, set budgets, visualize where your money goes, and add expenses by typing in plain English.

### 🔗 Live Demo
**[diyamary111.pythonanywhere.com](https://diyamary111.pythonanywhere.com)**

---

## ✨ Features

- **Dashboard overview** — see total spent, daily average, top category, and transaction count at a glance
- **Interactive charts** — a category breakdown donut and a daily-spending line chart (powered by Chart.js)
- **Smart expense entry** — type naturally like *"spent 450 on biryani yesterday"* and the app fills in the amount, category, and date automatically
- **Auto-categorization** — item names are sorted into categories on their own
- **Spending insights** — plain-English observations like *"Food is up 30% from last month"* and budget-pace projections
- **Budgets** — set an overall monthly limit plus optional per-category caps, with color-coded progress bars (green → amber → red)
- **Search & filter** — find expenses by name or filter by category
- **Monthly history** — browse spending from any past month with a calendar picker
- **Clean, responsive UI** — a light blue-and-white design that works on mobile and desktop

---

## 🛠️ Built With

- **Django** — backend framework
- **SQLite** — database
- **Chart.js** — data visualizations
- **WhiteNoise** — static file serving
- **HTML / CSS / JavaScript** — frontend
- Pure-Python natural-language parsing (no external AI API required)

---

## 🚀 Running Locally

1. **Clone the repo**
   ```bash
   git clone https://github.com/diyamarygeorge/smart_expense_tracker.git
   cd smart_expense_tracker
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a login account**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the server**
   ```bash
   python manage.py runserver
   ```

7. Open **http://127.0.0.1:8000/** in your browser.

---

## 📝 Notes

- The natural-language expense parser runs fully offline using regex and keyword matching — no API keys needed.
- Built as a personal project to learn Django, deployment, and full-stack development.

---

Made by [Diya Mary George](https://github.com/diyamarygeorge)
