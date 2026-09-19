# Sixth_Sense
A caregiver assistance tool to sense and address emotional shifts

Current state: Partially functional, built on simulated EEG data until we have the real thing.

---

# How to Run the Application

## 1. Install dependencies

From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit pandas numpy scipy brainflow
```

**Note:** If using Windows, run the following command for the second line instead.

```bash
.venv\Scripts\activate
```

If you already have a venv, just activate it and run the pip install line above.

## 2. Run the app

From repo root:

```bash
python -m streamlit run real-time-bci-stream/app.py
```

Browser opens automatically at `http://localhost:8501`.

## 3. Use it

1. Click **Start session**.
2. Click **Generate sample** — creates a simulated EEG window and scores it.
3. Adjust the comfort slider, click **Save result** to log it to `history.csv`.
4. Click **Stop session** when done.

## Files

- `simulated_data.py` — generates fake 8-channel EEG windows
- `data_processing.py` — extracts band-power features, computes discomfort score
- `app.py` — Streamlit UI

Real OpenBCI Cyton setup: see [`cyton_setup_instructions.md`](./cyton_setup_instructions.md).

---

# 🧠 Welcome to the Fall 2026 SURGE Neuro Hackathon!

Welcome to the **SURGE Neuro Hack Fall 2026**, where you'll get hands-on experience developing Brain-Computer Interfaces (BCIs) and analyzing neural data. Over the course of this weekend, you'll work in teams to prototype applications using EEG data. 

<details>
<summary>Table of Contents</summary>

## Table of Contents

- [🧠 Welcome to the Fall 2026 SURGE Neuro Hackathon!](#-welcome-to-the-fall-2026-surge-neuro-hackathon)
  - [Table of Contents](#table-of-contents)
- [General Information:](#general-information)
  - [Support \& Collaboration](#support--collaboration)
  - [Hackathon Schedule](#hackathon-schedule)
  - [Rules:](#rules)
- [🏆 Challenge Streams](#-challenge-streams)
  - [**1️⃣ Brain-Controlled Applications (Real-Time BCI)**](#1️⃣-brain-controlled-applications-real-time-bci)
    - [Real-Time BCI Deliverables](#real-time-bci-deliverables)
  - [**2️⃣ AI \& Machine Learning (Offline EEG Data Analysis)**](#2️⃣-ai--machine-learning-offline-eeg-data-analysis)
    - [Offline EEG Data/ML Deliverables](#offline-eeg-dataml-deliverables)
  - [**3️⃣ Hardware Hacking (EEG Hardware \& Embedded Systems)**](#3️⃣-hardware-hacking-eeg-hardware--embedded-systems)
    - [Hardware Hacking Deliverables](#hardware-hacking-deliverables)
- [📩 Submission Information](#-submission-information)
    - [Submission Process](#submission-process)
- [📌 Getting Started](#-getting-started)
    - [**1️⃣ Clone this Repository**](#1️⃣-clone-this-repository)
    - [**2️⃣ Install Dependencies**](#2️⃣-install-dependencies)
    - [**3️⃣ Choose Your Challenge Stream and Get Hacking!**](#3️⃣-choose-your-challenge-stream-and-get-hacking)
- [Don't know where to start? Check this out!](#dont-know-where-to-start-check-this-out)
- [Repository Table of Contents](#repository-table-of-contents)
  - [📂 Neurohack-Fall-2026](#-neurohack-fall-2026)
    - [📂 getting-setup - Instructions on how to setup python](#-getting-setup---instructions-on-how-to-setup-python)
    - [📂 real-time-bci-stream – Resources \& starter code for real-time EEG applications](#-real-time-bci-stream--resources--starter-code-for-real-time-eeg-applications)
    - [📂 offline-analysis-stream – Resources \& starter code for EEG data analysis](#-offline-analysis-stream--resources--starter-code-for-eeg-data-analysis)
    - [📂 resources – Learning materials and references](#-resources--learning-materials-and-references)
</details>

---
# General Information:

## Support & Collaboration
- Join the **#neurohack-fall-2026** channel on the [SURGE Discord server](https://discord.gg/jvkwKfERt) to ask questions, share ideas, and collaborate with other participants.
- Refer back to the [introduction presentation](https://docs.google.com/presentation/d/1Kv9ZSb0_6BqbbZlZWzYRzQ__WZipsEUCZKcd4CUvxyY/edit?usp=sharing)
- Reach out directly to me at [mascini.max@dal.ca](mailto:mascini.max@dal.ca)! (Please keep in mind I may be busy helping other teams, so I may not respond immediately)

## Hackathon Schedule

- **Day 1 (Friday 5:00pm-8:00pm):** Introduction to BCI, EEG, and Team Formation
- **Day 2 (Saturday 9:00am-4:00pm):** Hacking!
- **Day 3 (Sunday 9:00am-4:00pm):** Project wrap-up & submission, team presentations, and judging!
  - Submission Deadline: Sunday @ 1:00 PM
  - Presentations: 2:30 PM - 4:00 PM

## Rules:
1. You are free to use any hardware or software tools you like, but we recommend using the resources provided in this repository.
2. You may work in teams of up to 4 people. Individual submissions are also allowed.
3. All work must be done during the hackathon period (Friday to Sunday).
4. You must submit your project by the deadline to be eligible for judging.
5. All team members must be present and speak during the teams' presentation to be eligible for a prize.
6. You are allowed to - even encouraged to use AI tools (e.g., ChatGPT, GitHub Copilot) to assist with coding, brainstorming, and problem-solving. **However, it is your responsibility to ensure that you understand and can explain all of your work!**
7. Have fun and be creative!

---

# 🏆 Challenge Streams
We have **three challenge tracks** you can choose from:

## **1️⃣ Brain-Controlled Applications (Real-Time BCI)**
**🎯 Challenge & Goal:** Develop an application where EEG signals **control an interaction or interface** in real time. Use real-time EEG to build a brain-controlled game, assistive tool, interactive experience, or whatever you brainstorm!

**Example Ideas:**
   - A **Mind-controlled game**
   - A **An EEG-controlled communication device**
   - A **mind-controlled music device**

### Real-Time BCI Deliverables

- **Project Presentation** (10 minutes max.) - See the [rubric for details.](./resources/Judging_rubrics.pdf) A general template for your presentation should include:
  -  Problem Statement & Motivation  
  - System Design & Implementation 
  - A live Demonstration (or a pre-recorded demo if real-time is not possible)  
  - Results & Interpretation (system performance, user interaction)
  - Challenges & Future Work
- **Code Repository** (GitHub or Zip file) – Should include: 
  - Your code, presentation and instructions for running the project (a readme file)


## **2️⃣ AI & Machine Learning (Offline EEG Data Analysis)**
**🎯 Challenge & Goal:** Analyze pre-recorded EEG data to extract insights, perform statistics, classify brain signals/states, or detect anomalies.

**BCI Dataset:** For this stream we have provided three datasets of EEG recordings from participants subjected to various experimental conditions designed to elicit specific neural responses. For more information on the provided dataset, please refer to the [dataset description](./offline-analysis-stream/dataset_description.md).
- **You may find and use a different, publicly available dataset for your analysis**. However, if you choose to use another dataset, volunteers may not be able to provide as much support.

### Offline EEG Data/ML Deliverables

- **Project Presentation** (10 minutes max.) - see the [rubric for details.](./resources/Judging_rubrics.pdf) A general template for your presentation should include:
  - Problem Statement & Motivation  
  - What you did with the data (preprocessing, analysis, modeling) 
  - Results & Interpretation (accuracy, feature importance, visualization of findings, etc.)  
  - Challenges & Future Work  
- **Code Repository** (GitHub or Zip file) – Should include:  
  - Your code/analyses, presentation and instructions for running the project (a readme file)

## **3️⃣ Hardware Hacking (EEG Hardware & Embedded Systems)**
**🎯 Challenge & Goal:** Design, build, or modify EEG hardware to improve signal acquisition, create a novel sensing device, or interface custom hardware with a BCI pipeline.

**Example Ideas:**
   - A **custom EEG electrode array or headset**
   - A **hardware-accelerated signal processing pipeline**
   - A **low-cost, DIY EEG amplifier or biosignal interface**

### Hardware Hacking Deliverables

- **Project Presentation** (10 minutes max.) - See the [rubric for details.](./resources/Judging_rubrics.pdf) A general template for your presentation should include:
  - Problem Statement & Motivation
  - Hardware Design & Implementation (schematics, components, build process)
  - A live Demonstration (or a pre-recorded demo)
  - Results & Interpretation (signal quality, performance benchmarks)
  - Challenges & Future Work
- **Code Repository** (GitHub or Zip file) – Should include:
  - Your code, schematics/CAD files, and a README with build and usage instructions

---

# 📩 Submission Information

- **Submission Deadline: Sunday, 1:00 PM**
- **Judging Format:** A **short presentation** followed by a **5-minute Q&A** session from the judges.
  - Order of team presentations will be decided at random.
- **Judging Criteria:** Projects will be evaluated based on the [rubrics provided for each challenge stream.](./resources/Judging_rubrics.pdf)
- **Prizes:** The top-scoring team will receive $500 to be split among the group equally; 2nd and 3rd place teams will get bragging rights, a great addition to your CV, and sweet SURGE swag prizes!

### Submission Process
- **How to Submit:**  
  - Upload your presentation, code, reports, and any other relevant files to your Github repository.
    - If files are too large, or you don't have a Github repository, you can submit a zip file.
    - Ensure it includes a *README* explaining about (and how to run/use) your project. 
  - **[Submit through the submission form](https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=mRm4YH8LLUGSo-F9iunj4H7FrINmspNAj3XHyveOfoJUNEpIMDdMRDVNUDlXVVdQTkpNVDBEMk9QSy4u)**
- **NOTE:** If you submit multiple times, only your most recent submission made before the submission deadline (1:00 pm on Sunday) will be considered. Submissions received after the deadline will not be accepted.  

---

# 📌 Getting Started
### **1️⃣ Clone this Repository**
```bash
git clone https://github.com/SURGE-NeuroTech-Club/Neurohack-Fall-2026.git
cd <Neurohack-Fall-2026>
```

### **2️⃣ Install Dependencies**
Navigate to [getting-setup/python_setup.md](./getting-setup/python_setup.md) for instructions on how to setup the provided miniforge `Brainhack` environment.

Alternatively, If you already have Python 3.12 installed, you will need to ensure you have the following packages installed if you want to run the provided scripts.
```bash
pip install scipy jupyterlab mne brainflow pyserial matplotlib
```

For Unity/Pygame-based projects, additional installations may be required.

### **3️⃣ Choose Your Challenge Stream and Get Hacking!**
Navigate to either:
- `real-time-bci-stream/` for the interactive applications stream.
- `offline-analysis-stream/` for the EEG data processing and machine learning stream.

---
# Don't know where to start? Check this out!
Dr. Aaron Newman produced a free online textbook that is a **fantastic place to start** learning about python, EEG signal processing, and brain-computer interfaces. It uses **MNE-Python** — the same library used in the provided example scripts — and covers preprocessing, artifact removal, ERPs, frequency analysis, and more!
- Full textbook: https://neuraldatascience.io/
  - Jump straight to python introduction: https://neuraldatascience.io/python/introduction/
  - Or to the EEG section: https://neuraldatascience.io/eeg/introduction/
---

# Repository Table of Contents
your_repo_name
## 📂 [Neurohack-Fall-2026](./)
- 📜 [README.md](./README.md) – Main documentation

### 📂 [getting-setup](./getting-setup/) - Instructions on how to setup python
- 📄 [python_setup.md](./getting-setup/python_setup.md) – Instructions on how to setup python
- 🐍 [brainhack_env.yaml](./getting-setup/brainhack_env.yaml) - Anaconda environment file with python 3.13 to get you started
- 🐍 [compatibility_brainhack_env.yaml](./getting-setup/compatibility_brainhack_env.yaml) - Anaconda environment file with python 3.10 to get you started

### 📂 [real-time-bci-stream](./real-time-bci-stream/) – Resources & starter code for real-time EEG applications
  - 📄 [cyton_setup_instructions.md](./real-time-bci-stream/cyton_setup_instructions.md) – Setup guide
  - 📂 [example-scripts/](./real-time-bci-stream/example-scripts/) – Starter code for real-time BCI

### 📂 [offline-analysis-stream](./offline-analysis-stream/) – Resources & starter code for EEG data analysis
  - 📄 [dataset_description.md](./offline-analysis-stream/dataset_description.md) – Information on the dataset
  - 📂 [sample-data/](./offline-analysis-stream/sample-data/) – Example EEG data
  - 📂 [example-scripts/](./offline-analysis-stream/example-scripts/) – Starter scripts for EEG analysis

### 📂 [resources](./resources/) – Learning materials and references
  - 📄 [bci_basics.md](./resources/bci_basics.md) – Introduction to BCI concepts
  - 📄 [useful_links.md](./resources/useful_links.md) – Reference materials and links
  - 📄 [judging_rubrics.pdf](./resources/Judging_rubrics.pdf) – Outline of deliverables for each stream & judging rubrics
