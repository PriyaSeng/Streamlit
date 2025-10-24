Here’s a **GitHub-ready project description** for your new Streamlit dashboard.
You can copy this directly into your repository’s **README.md** — it’s clear, professional, and beginner-friendly while showing impact and practical value.

---

# 🎓 Student Success Snapshot — Streamlit Dashboard

A lightweight, interactive dashboard built with **Streamlit** for visualizing and monitoring **student success metrics** such as GPA, retention, and engagement.
This beginner-friendly app is ideal for advisors, administrators, and education analytics teams who want quick insights without coding.

---

## 🌟 Features

✅ **Upload or use sample data**

* Works with CSV or Excel files
* Includes a demo dataset (`sample_student_success_80rows.csv`)

✅ **Interactive filters**

* Filter by **Program**, **Campus**, and **Term Range**

✅ **Key performance indicators (KPIs)**

* Total Students
* Average GPA
* Retention Rate (%)
* Average Engagement Score

✅ **Visual insights**

* 📊 *Average GPA by Program*
* 📈 *Retention Trend over Terms*

✅ **Advising Priority Table**

* Highlights students with low engagement or retention risk
* Simple logic: engagement < 55 or not retained or flagged for advising

✅ **Exportable Data**

* Download filtered data in one click (`student_success_filtered.csv`)

---

## 🛠️ Tech Stack

* **Python 3.10+**
* **Streamlit** (UI)
* **Pandas** (data processing)
* **Plotly Express** (visualizations)
* **OpenPyXL** (Excel support)

---

## 🚀 Getting Started

### 1️⃣ Clone the repository

```bash
git clone https://github.com/<your-username>/student-success-snapshot.git
cd student-success-snapshot
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the app

```bash
streamlit run app.py
```

### 4️⃣ Open in browser

Streamlit will open automatically (default: [http://localhost:8501](http://localhost:8501))

---

## 📂 Data Format

Your data should contain the following columns (use the included sample as a guide):

| Column             | Description                                     |
| ------------------ | ----------------------------------------------- |
| `student_id`       | Unique identifier for each student              |
| `term_date`        | Academic term or course date                    |
| `program`          | Academic program name                           |
| `campus`           | Campus or delivery mode                         |
| `course`           | Course code                                     |
| `credits`          | Credit hours                                    |
| `grade_points`     | Numeric GPA value (0–4 scale)                   |
| `engagement_score` | Student engagement level (0–100)                |
| `retained`         | Boolean (True = retained, False = not retained) |
| `advising_flag`    | "Yes"/"No" flag for advising need               |

---

## 🧠 How It Works

1. Load data → Streamlit automatically detects column types.
2. Apply filters → Dashboard recalculates KPIs & charts in real-time.
3. Drill down → Identify at-risk students for proactive advising.
4. Export → Download a filtered CSV for reports or follow-up actions.

---

## 💡 Example Use Case

> “In just one click, advisors can see which programs have lower average GPA or retention, track changes over time, and export the list of students who may need outreach.”

---

## 📸 Screenshots (optional)

| KPI Summary                                 | Retention Trend                                     |
| ------------------------------------------- | --------------------------------------------------- |
| ![KPI summary](screenshots/kpi_summary.png) | ![Retention trend](screenshots/retention_trend.png) |

---

## 📜 License

MIT License © 2025 Priya Arvind Singh Sengar

---

