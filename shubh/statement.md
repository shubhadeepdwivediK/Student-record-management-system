# Problem Statement – Student Record Management System (SRMS)

## Problem statement
Many small departments and coaching centres still keep student details, marks and results in
scattered spreadsheets or paper registers. This causes duplicate entries, typing mistakes
(e.g. marks above 100), slow CGPA calculation, no access control, and no audit trail of who
changed what. There is a need for a simple, reliable, offline tool that stores student records
in one place, validates every entry, calculates results consistently and produces reports.

## Scope of the project
**In scope**
- Secure login with two roles (Admin, Faculty)
- CRUD for students and courses
- Recording marks per student per course, letter grades and credit-weighted CGPA
- Reports: course statistics, rank list, department summary, CSV import/export
- Input validation, error handling and file-based audit logging
- Automated unit tests

**Out of scope**
- Web/mobile UI, online multi-user access, fee/attendance management, email notifications

## Target users
| User | Needs |
|------|-------|
| Administrator | Manage users, delete records, view all reports |
| Faculty / staff | Add and update students, courses and marks; view reports |
| Students (indirect) | Get correct transcripts and rankings |

## High-level features
1. **Student management** – add, view, update, delete, search, filter and sort
2. **Course & grade management** – course catalogue, marks entry, transcripts, course grade sheets
3. **Reports & analytics** – mean/median/std-dev/pass-rate, grade distribution, rank list with ties, department summary
4. **Import / export** – bulk student import from CSV (bad rows reported, not fatal), export students and transcripts
5. **Authentication & roles** – salted PBKDF2 password hashing, permission checks on every sensitive action
6. **Logging** – rotating log file of logins, changes and errors
