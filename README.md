# 🏥 ESKD Risk Classification Web App

A full-stack **Django web application** for patient management and **End-Stage Kidney Disease (ESKD)** risk classification based on clinical and laboratory data.  
This project integrates data entry, risk prediction through a machine-learning model, and visualization of patient-specific results — all within a single, secure platform.

---

## 📋 Table of Contents

1. [Overview](#overview)  
2. [Key Features](#key-features)  
3. [Actors and Roles](#actors-and-roles)  
4. [System Architecture](#system-architecture)  
5. [Production Pipeline](#production-pipeline)  
6. [Database and Storage](#database-and-storage)  
7. [Technology Stack](#technology-stack)  
8. [Deployment Notes](#deployment-notes)  
9. [Security and Compliance](#security-and-compliance)  
10. [Future Improvements](#future-improvements)  
11. [License](#license)

---

## 🧭 Overview

This Django application is designed to support healthcare professionals in managing patient records and predicting the likelihood of progression to **End-Stage Kidney Disease (ESKD)**.  
It combines **clinical data management**, **automated classification**, and **data visualization** in a single interface.

### Main objectives
- Centralize patient information and laboratory results.  
- Enable physicians to run an integrated **ESKD classification model**.  
- Store predictions and visualize them in the patient dashboard.  
- Provide an extendable foundation for research and hospital integration.

---

## ✨ Key Features

- **User authentication and authorization** (via Django Auth).  
- **Patient CRUD** (Create, Read, Update, Delete) operations.  
- **ESKD risk prediction** using an integrated ML classifier.  
- **Dynamic dashboard** with patient history and risk visualization.  
- **Local storage** for medical reports and uploaded images.  
- **Audit logs** for predictions and user actions.  

---

## 👥 Actors and Roles

| Actor | Description | Permissions |
|--------|--------------|-------------|
| **Administrator** | Manages users, roles, and global configurations. | Full access (user and system management). |
| **Physician / Clinician** | Manages patient records and performs risk classification. | Create/update patients, trigger ML predictions, view results. |
| **Researcher** | Analyzes aggregated or anonymized results. | Read-only access to data summaries and statistics. |
| **Patient (optional)** | Can view their own data (if allowed). | Read-only self-access. |

---

# ⚙️ System Architecture

Django acts as both the **frontend and backend** framework.

## Architecture Overview
```mermaid
flowchart TD
    A[User (Browser)] -->|HTTPS Request| B[NGINX Reverse Proxy]
    B -->|WSGI Socket| C[Gunicorn Application Server]
    C --> D[Django Framework (Backend + Frontend)]
    D -->|ORM Query| E[(SQLite Database)]
    D -->|Prediction Request| F[ESKD Classifier (Python Model)]
    F -->|Result| D
    D -->|Template Rendering| G[HTML Page (Frontend)]
    D --> H[(Local Media Storage)]
    D -.-> I[Monitoring / Logs]
    G -->|HTTP Response| B --> A
```

## 🖼️ Some Screenshots

### 🔐 Dashboard Page

<p align="center">
<img src="docs/images/dashboard.png" alt="Dashboard Page" width="60%">
</p>

### 🏥 Patient List

<p align="center">
<img src="docs/images/patient_list.png" alt="Patients List" width="80%">
</p>

### 🧠 Patient Details

<p align="center">
<img src="docs/images/patient_details.png" alt="Patient Details" width="80%">
</p>

### 🤖 ESKD Predictor

<p align="center">
<img src="docs/images/prediction_result.png" alt="ESKD AI Predictor" width="80%">
</p>