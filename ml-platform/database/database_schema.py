import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "sentronix.db"


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def migrate_columns(cursor, table_name, expected_columns):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_cols = {row[1] for row in cursor.fetchall()}
    for col_name, col_type in expected_columns.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")


def init_database():
    """Initializes the complete Sentronix AI relational schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users table (with OTP support)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            is_verified INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            otp_code TEXT,
            otp_expires_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # 2. Environments table (Multi-environment architecture)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS environments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            location TEXT,
            enabled_features TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # 3. Camera Groups
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS camera_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            environment_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (environment_id) REFERENCES environments (id) ON DELETE CASCADE
        )
    """
    )

    # 4. Cameras
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            environment_id INTEGER,
            group_id INTEGER,
            camera_name TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'webcam',
            source_url TEXT DEFAULT '0',
            location TEXT,
            status TEXT DEFAULT 'online',
            ai_enabled INTEGER DEFAULT 1,
            processing_fps INTEGER DEFAULT 10,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (environment_id) REFERENCES environments (id),
            FOREIGN KEY (group_id) REFERENCES camera_groups (id)
        )
    """
    )

    # 5. People Registry (Students, Staff, Visitors)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            environment_id INTEGER,
            identifier TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            department TEXT,
            class_grade TEXT,
            photo_url TEXT,
            is_enrolled INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (environment_id) REFERENCES environments (id)
        )
    """
    )

    # 6. Face Embeddings (Separated from raw detection)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS face_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            embedding_json TEXT NOT NULL,
            feature_version TEXT DEFAULT 'v1',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES people (id) ON DELETE CASCADE
        )
    """
    )

    # 7. Attendance Records
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            camera_id INTEGER,
            environment_id INTEGER,
            timestamp TEXT NOT NULL,
            confidence REAL NOT NULL,
            status TEXT DEFAULT 'PRESENT',
            presence_seconds INTEGER DEFAULT 5,
            evidence_snapshot TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES people (id),
            FOREIGN KEY (camera_id) REFERENCES cameras (id),
            FOREIGN KEY (environment_id) REFERENCES environments (id)
        )
    """
    )

    # 8. Rules Engine Configuration
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            environment_id INTEGER,
            name TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            conditions_json TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'MEDIUM',
            cooldown_seconds INTEGER DEFAULT 30,
            is_enabled INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (environment_id) REFERENCES environments (id)
        )
    """
    )

    # 9. Detections (Raw AI output)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            camera_id TEXT NOT NULL,
            object TEXT NOT NULL,
            confidence REAL NOT NULL,
            bbox TEXT,
            track_id INTEGER
        )
    """
    )

    # 10. Events (Interpreted occurrences)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            environment_id INTEGER,
            camera_id TEXT,
            rule_id INTEGER,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'INFO',
            description TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            evidence_url TEXT,
            status TEXT DEFAULT 'NEW',
            FOREIGN KEY (rule_id) REFERENCES rules (id)
        )
    """
    )

    # 11. Alerts (Actionable incidents requiring human operator triage)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            object TEXT NOT NULL,
            priority TEXT NOT NULL,
            confidence REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            acknowledged_by TEXT,
            resolution_notes TEXT,
            camera_id TEXT,
            event_id INTEGER,
            FOREIGN KEY (event_id) REFERENCES events (id)
        )
    """
    )

    # 12. Notifications (In-app, Email, Webhook)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            priority TEXT DEFAULT 'NORMAL',
            channel TEXT DEFAULT 'in_app',
            is_read INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL
        )
    """
    )

    # 13. Audit Logs
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            details TEXT,
            timestamp TEXT NOT NULL
        )
    """
    )

    # Apply column migrations for existing legacy tables
    migrate_columns(
        cursor,
        "cameras",
        {
            "environment_id": "INTEGER",
            "group_id": "INTEGER",
            "source_type": "TEXT DEFAULT 'webcam'",
            "source_url": "TEXT DEFAULT '0'",
            "ai_enabled": "INTEGER DEFAULT 1",
            "processing_fps": "INTEGER DEFAULT 10",
            "created_at": "TEXT",
        },
    )

    migrate_columns(
        cursor,
        "alerts",
        {
            "acknowledged_by": "TEXT",
            "resolution_notes": "TEXT",
            "camera_id": "TEXT",
            "event_id": "INTEGER",
        },
    )

    migrate_columns(cursor, "detections", {"track_id": "INTEGER"})

    conn.commit()
    conn.close()
    print("Sentronix AI Relational Database initialized successfully.")


def seed_default_environment_and_rules():
    """Seeds baseline School/College environment, cameras, people, and safety rules."""
    conn = get_connection()
    cursor = conn.cursor()

    # Seed Admin User if none exists (password: admin123, hash created via simple sha256 or bcrypt)
    import hashlib

    admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, username, email, full_name, role, hashed_password, is_verified, is_active)
        VALUES (1, 'admin', 'admin@sentronix.ai', 'System Administrator', 'admin', ?, 1, 1)
    """,
        (admin_pw,),
    )

    # Seed School Environment
    features = json.dumps(
        [
            "face_detection",
            "face_recognition",
            "attendance",
            "dress_code",
            "restricted_area",
            "prohibited_activity",
            "alerts",
            "reports",
        ]
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO environments (id, name, type, description, location, enabled_features, is_active)
        VALUES (1, 'Greenwood Campus', 'School', 'Primary campus security and student attendance', 'Main Block', ?, 1)
    """,
        (features,),
    )

    # Seed Camera Groups
    cursor.execute(
        """
        INSERT OR IGNORE INTO camera_groups (id, environment_id, name, description)
        VALUES (1, 1, 'Main Entrance', 'Main campus entry gate and turnstiles')
    """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO camera_groups (id, environment_id, name, description)
        VALUES (2, 1, 'Classroom Corridor', 'Grade 10 & 11 wing hallways')
    """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO camera_groups (id, environment_id, name, description)
        VALUES (3, 1, 'Server & Labs', 'Restricted IT and Chemistry laboratories')
    """
    )

    # Seed Cameras
    cursor.execute(
        """
        INSERT OR IGNORE INTO cameras (id, environment_id, group_id, camera_name, source_type, source_url, location, status, ai_enabled)
        VALUES (1, 1, 1, 'Entrance Cam 01', 'webcam', '0', 'Main Gate Gate-A', 'online', 1)
    """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO cameras (id, environment_id, group_id, camera_name, source_type, source_url, location, status, ai_enabled)
        VALUES (2, 1, 2, 'Corridor Cam 02', 'test_stream', 'sample_corridor.mp4', 'Classroom Block B', 'online', 1)
    """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO cameras (id, environment_id, group_id, camera_name, source_type, source_url, location, status, ai_enabled)
        VALUES (3, 1, 3, 'Lab Restricted Cam 03', 'test_stream', 'sample_lab.mp4', 'Chemistry Lab 2', 'online', 1)
    """
    )

    # Seed Demo Enrolled People (Students and Staff)
    cursor.execute(
        """
        INSERT OR IGNORE INTO people (id, environment_id, identifier, name, role, department, class_grade, is_enrolled, status)
        VALUES (1, 1, 'STU-101', 'Aarav Sharma', 'student', 'Science', 'Grade 10-A', 1, 'active')
    """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO people (id, environment_id, identifier, name, role, department, class_grade, is_enrolled, status)
        VALUES (2, 1, 'STU-102', 'Diya Patel', 'student', 'Science', 'Grade 10-A', 1, 'active')
    """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO people (id, environment_id, identifier, name, role, department, class_grade, is_enrolled, status)
        VALUES (3, 1, 'STF-501', 'Dr. Ramesh Kumar', 'staff', 'Faculty of Physics', 'Staff', 1, 'active')
    """
    )

    # Seed Baseline Safety & Attendance Rules
    rule1_cond = json.dumps({"target": "fire", "min_confidence": 0.65})
    cursor.execute(
        """
        INSERT OR IGNORE INTO rules (id, environment_id, name, rule_type, conditions_json, severity, cooldown_seconds, is_enabled)
        VALUES (1, 1, 'Campus Fire & Hazard Detection', 'prohibited_activity', ?, 'CRITICAL', 60, 1)
    """,
        (rule1_cond,),
    )

    rule2_cond = json.dumps({"target": "weapon", "min_confidence": 0.60})
    cursor.execute(
        """
        INSERT OR IGNORE INTO rules (id, environment_id, name, rule_type, conditions_json, severity, cooldown_seconds, is_enabled)
        VALUES (2, 1, 'Prohibited Weapon Detection', 'prohibited_activity', ?, 'CRITICAL', 60, 1)
    """,
        (rule2_cond,),
    )

    rule3_cond = json.dumps(
        {"target": "person", "group": "Server & Labs", "time_window": "after_hours"}
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO rules (id, environment_id, name, rule_type, conditions_json, severity, cooldown_seconds, is_enabled)
        VALUES (3, 1, 'Restricted Zone Intrusion', 'restricted_zone', ?, 'HIGH', 45, 1)
    """,
        (rule3_cond,),
    )

    rule4_cond = json.dumps(
        {
            "target": "face_match",
            "min_presence_sec": 3,
            "attendance_window": "08:00-16:00",
        }
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO rules (id, environment_id, name, rule_type, conditions_json, severity, cooldown_seconds, is_enabled)
        VALUES (4, 1, 'Daily Campus Student Attendance', 'attendance', ?, 'LOW', 300, 1)
    """,
        (rule4_cond,),
    )

    conn.commit()
    conn.close()
    print("Sentronix AI seed data inserted successfully.")


if __name__ == "__main__":
    init_database()
    seed_default_environment_and_rules()
