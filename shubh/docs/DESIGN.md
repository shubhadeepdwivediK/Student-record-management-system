# Design Document

Diagrams are written in [Mermaid](https://mermaid.js.org) – GitHub renders them automatically.
For the PDF report, paste each block into https://mermaid.live and export as PNG.

## 1. Non-functional requirements
| # | Category | Requirement | How it is met |
|---|----------|-------------|---------------|
| 1 | Security | Passwords never stored in plain text; only authorised roles may delete or manage users | Salted PBKDF2-SHA256 (200k iterations), `hmac.compare_digest`, role checks (`User.require`) |
| 2 | Reliability / Error handling | Bad input or DB errors must not crash the app or corrupt data | Validators, custom exceptions, transactions with rollback, foreign keys & CHECK constraints |
| 3 | Usability | Clear menus, re-prompt on invalid input, confirmation before deletes | `ask()` retry loop, `confirm()`, friendly messages |
| 4 | Maintainability | Layered, modular code that is easy to extend and test | Presentation → Service → Repository → DB separation; 37 unit tests |
| 5 | Logging | Trace logins, changes and errors | Rotating log file `logs/srms.log` |
| 6 | Performance | Common operations < 1 s for ~10,000 students | Indexes on department and grade foreign keys, parameterised queries |
| 7 | Portability / Resource efficiency | Runs anywhere with Python, no installs | Standard library only, SQLite single file |

## 2. System architecture
```mermaid
flowchart TB
    U([User: Admin / Faculty]) --> CLI[CLI - cli.py<br/>menus, prompts]
    CLI --> AUTH[AuthService<br/>auth.py]
    CLI --> SVC[Services - services.py<br/>Student / Course / Grade]
    CLI --> REP[ReportService<br/>reports.py]
    SVC --> VAL[validators.py]
    AUTH --> VAL
    SVC --> REPO[Repositories<br/>repository.py]
    REP --> SVC
    REP --> REPO
    REPO --> DB[(SQLite<br/>database.py)]
    AUTH --> DB
    REP --> CSV[/CSV files/]
    CLI -.-> LOG[[logger.py -> logs/srms.log]]
    SVC -.-> LOG
    AUTH -.-> LOG
```

## 3. Workflow diagram
```mermaid
flowchart TD
    A([Start]) --> B{Any users<br/>in DB?}
    B -- No --> C[Create admin account]
    B -- Yes --> D[Login]
    C --> E
    D --> D2{Valid?}
    D2 -- No, attempts left --> D
    D2 -- No, 3 failures --> Z([Exit])
    D2 -- Yes --> E[Main menu]
    E --> F[Students]
    E --> G[Courses]
    E --> H[Grades]
    E --> I[Reports]
    E --> J[Users - admin only]
    F & G & H & I & J --> K[Prompt + validate input]
    K --> L{Permission OK?}
    L -- No --> M[Show error] --> E
    L -- Yes --> N[Service -> Repository -> DB]
    N --> O[Show result / log event] --> E
    E --> Z
```

## 4. Use case diagram
```mermaid
flowchart LR
    Admin([Admin]) --- UC1(Login)
    Faculty([Faculty]) --- UC1
    Faculty --- UC2(Add / update students)
    Faculty --- UC3(Manage courses)
    Faculty --- UC4(Record marks)
    Faculty --- UC5(View transcripts)
    Faculty --- UC6(View reports)
    Faculty --- UC7(Import / export CSV)
    Admin --- UC2
    Admin --- UC3
    Admin --- UC4
    Admin --- UC5
    Admin --- UC6
    Admin --- UC7
    Admin --- UC8(Delete students / courses / grades)
    Admin --- UC9(Manage users)
```

## 5. Sequence diagram – recording a grade
```mermaid
sequenceDiagram
    actor F as Faculty
    participant CLI
    participant GS as GradeService
    participant V as validators
    participant SS as StudentService / CourseService
    participant GR as GradeRepository
    participant DB as SQLite
    F->>CLI: Choose "Record marks"
    CLI->>CLI: user.require("write")
    F->>CLI: roll no, course, marks, semester
    CLI->>GS: record(roll, course, marks, sem)
    GS->>SS: get(roll), get(course)
    SS->>DB: SELECT student / course
    DB-->>SS: rows (or NotFoundError)
    GS->>V: marks(), semester()
    V-->>GS: cleaned values (or ValidationError)
    GS->>GR: upsert(student_id, course_id, sem, marks)
    GR->>DB: INSERT ... ON CONFLICT DO UPDATE
    GS-->>CLI: {grade, points}
    CLI-->>F: "Saved: marks -> grade S"
```

## 6. Class diagram
```mermaid
classDiagram
    class Student { +int id; +str roll_no; +str name; +str email; +str phone; +str department; +int year }
    class Course { +int id; +str code; +str title; +int credits }
    class User { +str username; +str role; +can(action); +require(action) }
    class Database { +connection(); +initialise() }
    class StudentRepository { +add(); +get_by_roll(); +update(); +delete(); +list_all(); +search() }
    class CourseRepository { +add(); +get_by_code(); +update(); +delete(); +list_all() }
    class GradeRepository { +upsert(); +delete(); +for_student(); +for_course(); +all_with_credits() }
    class StudentService { +create(); +get(); +update(); +delete(); +list(); +search() }
    class CourseService { +create(); +get(); +update(); +delete(); +list() }
    class GradeService { +record(); +remove(); +transcript(); +course_sheet() }
    class ReportService { +course_statistics(); +rank_list(); +department_summary(); +export_students(); +export_transcript(); +import_students() }
    class AuthService { +register(); +login(); +has_users(); +list_users() }
    class App { +login(); +main_menu() }
    StudentService --> StudentRepository
    CourseService --> CourseRepository
    GradeService --> GradeRepository
    GradeService --> StudentService
    GradeService --> CourseService
    ReportService --> GradeService
    ReportService --> StudentService
    StudentRepository --> Database
    CourseRepository --> Database
    GradeRepository --> Database
    AuthService --> Database
    AuthService ..> User
    StudentRepository ..> Student
    CourseRepository ..> Course
    App --> StudentService
    App --> CourseService
    App --> GradeService
    App --> ReportService
    App --> AuthService
```

## 7. ER diagram
```mermaid
erDiagram
    STUDENTS ||--o{ GRADES : has
    COURSES  ||--o{ GRADES : "graded in"
    STUDENTS { int id PK
               string roll_no UK
               string name
               string email UK
               string phone
               string department
               int year
               datetime created_at }
    COURSES  { int id PK
               string code UK
               string title
               int credits }
    GRADES   { int id PK
               int student_id FK
               int course_id FK
               int semester
               float marks }
    USERS    { int id PK
               string username UK
               string password_hash
               string salt
               string role
               datetime created_at }
```
`GRADES` has a composite unique constraint `(student_id, course_id)` and `ON DELETE CASCADE` on both foreign keys.

## 8. Design decisions & rationale
- **Layered architecture** – UI, business rules and SQL are separate, so each can be tested or replaced alone (e.g. swap the CLI for a web UI without touching services).
- **SQLite** – zero-setup, transactional, file-based; enough for a departmental tool.
- **Repository pattern** – all SQL in one file, parameterised to prevent SQL injection.
- **Dataclasses for models** – concise, typed, easy to convert to dicts/CSV.
- **Custom exceptions** – the CLI catches `SRMSError` and shows friendly text; unexpected errors are logged with a stack trace.
- **Upsert for grades** – re-entering marks corrects the record instead of failing.
- **Credit-weighted CGPA** – matches how university CGPA is really computed.
- **Standard library only** – nothing to install, fewer things to break.
