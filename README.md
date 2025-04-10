# ⚡ PowerUpResume (PUR)

**PowerUpResume (PUR)** is an AI-powered resume enhancement tool designed to **automate grammar correction, smart rephrasing, and impactful content transformation**. We’re building it as a **modular full-stack application** integrating NLP, frontend/backend architecture, and APIs to deliver a smooth and intelligent resume refinement experience.

---

### 🧠 What We’ve Built So Far

- ✅ **Grammar Correction** using `Gramformer` (BERT-based)
- 🔁 **Smart Rephrasing** powered by `T5 Transformer`
- 💪 **Action Verb Enhancement** to make experience bullet points strong and dynamic
- 📄 **PDF Text Extraction** using `pdfplumber`
- 📤 **Enhanced Resume Generation** using `reportlab` with improved formatting (in progress)

---

### 🔧 Why We Built It

We initially explored **Microsoft Power Automate** for text extraction, but quickly realized:
- It's **too slow** for our needs
- Heavily dependent on **paid add-ons**
- Complex for simple text extraction tasks

So, we decided to build our own **custom solution**:
- A basic **frontend** where users can upload their resume
- A flexible **backend** for text extraction, NLP enhancements, and downloadable output

---

### 🛠️ Tech Stack

| Layer        | Tech Used                            |
|--------------|---------------------------------------|
| 🧠 ML / NLP   | Gramformer, HuggingFace Transformers |
| 🐍 Backend    | Python, pdfplumber, reportlab        |
| 🌐 Frontend   | HTML, JS (React planned)             |
| 🔗 APIs       | FastAPI / Flask (in progress)         |

---

### 🚧 Work In Progress

We’re actively developing multiple parts of the project:

- [x] NLP-based sentence enhancement
- [x] Basic CLI version for PDF upload and output
- [ ] Resume format preservation in output PDF
- [ ] Frontend UI for uploading resumes
- [ ] API integration for modular features
- [ ] Authentication and user dashboard
- [ ] LinkedIn profile enhancement extension

---

### 🧪 How to Try (CLI Version)

1. Add your resume file (e.g. `Aryan_CV_LINKEDIN.pdf`) to the project root.
2. Run:
   ```bash
   python resume_enhancer.py
   ```
3. Get the enhanced version as a new downloadable PDF!

---

### 🌱 Our Vision

> _We aim to make resume building and enhancement more accessible, intelligent, and efficient using cutting-edge AI and design thinking._

Whether you're a student, job seeker, or working professional — **PowerUpResume (PUR)** will help you **stand out** with clarity and confidence.

---

Want a badge section, contributing guide, or live deployment note too? Just let me know!
