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
            zone TEXT DEFAULT 'General',
            assigned_function TEXT DEFAULT 'FACE_ATTENDANCE',
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
    migrate_columns(
        cursor,
        "cameras",
        {
            "assigned_function": "TEXT DEFAULT 'FACE_ATTENDANCE'",
            "zone": "TEXT DEFAULT 'General'",
        },
    )

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

    # Seed 5 Prominent Operational Environments
    env_features = json.dumps(
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

    environments_data = [
        (
            1,
            "Greenwood Defense Academy & University",
            "School",
            "Academic campus, lecture theaters, laboratories and student residential halls",
            "Academic Sector North",
            env_features,
            1,
        ),
        (
            2,
            "Apex Heavy Engineering & Chemical Plant",
            "Industry",
            "High-hazard industrial plant, automated assembly lines, hazardous storage, and boiler units",
            "Industrial Corridor South",
            env_features,
            1,
        ),
        (
            3,
            "Fortress Bravo Strategic Defense Perimeter",
            "Military",
            "High-security defense perimeter, ammunition depots, command bunkers, and radar watchtowers",
            "Tactical Sector 9 Red Zone",
            env_features,
            1,
        ),
        (
            4,
            "Metro General Hospital & Trauma Center",
            "Hospital",
            "Emergency ward, ICU corridors, pharmacy vaults, and surgical operation wings",
            "Central Health District",
            env_features,
            1,
        ),
        (
            5,
            "Titan Cybernetics Global Tech Park",
            "Corporate",
            "High-tech corporate campus, server farm data centers, and executive towers",
            "Silicon Cyber Park",
            env_features,
            1,
        ),
    ]

    for env in environments_data:
        cursor.execute(
            """
            INSERT OR REPLACE INTO environments (id, name, type, description, location, enabled_features, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            env,
        )

    # Seed 7 Tactical Camera Groups (Sectors)
    groups_data = [
        (
            1,
            1,
            "Sector 1 - Outer Perimeter & Security Fences",
            "High-security boundary fence, watchtowers, and infrared sensors",
        ),
        (
            2,
            1,
            "Sector 2 - Main Gate Checkpoints & Turnstiles",
            "Access control boom barriers, pedestrian turnstiles, and guard posts",
        ),
        (
            3,
            1,
            "Sector 3 - Corridors, Hallways & Walkways",
            "Internal thoroughfares, skybridges, stairwells, and elevator banks",
        ),
        (
            4,
            1,
            "Sector 4 - High-Value Vaults & Laboratories",
            "Restricted armory, server rooms, chemistry labs, and hazardous lockers",
        ),
        (
            5,
            1,
            "Sector 5 - Operational Workspaces & Plants",
            "Turbine halls, fabrication lines, robotic cells, and packaging floors",
        ),
        (
            6,
            1,
            "Sector 6 - Public Plazas & Assembly Grounds",
            "Parade squares, dining halls, sports stadiums, and auditoriums",
        ),
        (
            7,
            1,
            "Sector 7 - Logistics, Motor Pool & Parking",
            "Cargo bays, vehicle inspection points, underground parking, and fuel depots",
        ),
    ]

    for grp in groups_data:
        cursor.execute(
            """
            INSERT OR REPLACE INTO camera_groups (id, environment_id, name, description)
            VALUES (?, ?, ?, ?)
        """,
            grp,
        )

    # Seed Comprehensive Fleet of 80 Operational Cameras
    # Spec: (id, group_id, name, source_type, source_url, location, zone, assigned_function)
    FLEET_CAMERAS = [
        # Sector 2: Main Gate Checkpoints & Turnstiles (Cams 1-12)
        (
            1,
            2,
            "CAM-001 [Main Gate Checkpoint Alpha]",
            "webcam",
            "0",
            "Main Gate Alpha Checkpoint",
            "Gate Access",
            "FACE_ATTENDANCE",
        ),
        (
            2,
            1,
            "CAM-002 [Tactical Mobile Patrol Scout]",
            "mobile_ip",
            "http://192.168.1.50:8080/video",
            "Roving Tactical Scout",
            "Perimeter Patrol",
            "PERIMETER_INTRUSION",
        ),
        (
            3,
            2,
            "CAM-003 [Access Turnstile Bank 01]",
            "test_stream",
            "sample_corridor.mp4",
            "Turnstile Bank A",
            "Pedestrian Gate",
            "FACE_ATTENDANCE",
        ),
        (
            4,
            2,
            "CAM-004 [Access Turnstile Bank 02]",
            "test_stream",
            "sample_corridor.mp4",
            "Turnstile Bank B",
            "Pedestrian Gate",
            "FACE_ATTENDANCE",
        ),
        (
            5,
            2,
            "CAM-005 [Visitor Registration Kiosk]",
            "test_stream",
            "sample_corridor.mp4",
            "Security Reception",
            "Visitor Center",
            "FACE_ATTENDANCE",
        ),
        (
            6,
            2,
            "CAM-006 [Staff Fast-Track Turnstile]",
            "test_stream",
            "sample_corridor.mp4",
            "East Staff Gate",
            "Staff Access",
            "FACE_ATTENDANCE",
        ),
        (
            7,
            2,
            "CAM-007 [Guard Post Alpha Frontage]",
            "test_stream",
            "sample_corridor.mp4",
            "Main Gate Sentry Post",
            "Guard Post",
            "WEAPON_VIOLENCE",
        ),
        (
            8,
            2,
            "CAM-008 [Secondary Checkpoint Bravo]",
            "test_stream",
            "sample_corridor.mp4",
            "Gate Bravo Inbound",
            "Secondary Gate",
            "FACE_ATTENDANCE",
        ),
        (
            9,
            2,
            "CAM-009 [Vehicle Ingress Boom Barrier]",
            "test_stream",
            "sample_corridor.mp4",
            "Vehicle Gate North",
            "Vehicle Access",
            "ANPR_VEHICLES",
        ),
        (
            10,
            2,
            "CAM-010 [Vehicle Egress Boom Barrier]",
            "test_stream",
            "sample_corridor.mp4",
            "Vehicle Gate South",
            "Vehicle Access",
            "ANPR_VEHICLES",
        ),
        (
            11,
            2,
            "CAM-011 [Turnstile Egress Bank 01]",
            "test_stream",
            "sample_corridor.mp4",
            "Main Exit Hall",
            "Exit Turnstile",
            "FACE_ATTENDANCE",
        ),
        (
            12,
            2,
            "CAM-012 [Gate Attire Inspection Bay]",
            "test_stream",
            "sample_corridor.mp4",
            "Security Inspection Bay",
            "Uniform Inspection",
            "DRESS_CODE_PPE",
        ),
        # Sector 1: Outer Perimeter & Security Fences (Cams 13-24)
        (
            13,
            1,
            "CAM-013 [North Fence Infrared PTZ 1]",
            "test_stream",
            "sample_corridor.mp4",
            "North Boundary Line 1",
            "Outer Fence",
            "PERIMETER_INTRUSION",
        ),
        (
            14,
            1,
            "CAM-014 [North Fence Infrared PTZ 2]",
            "test_stream",
            "sample_corridor.mp4",
            "North Boundary Line 2",
            "Outer Fence",
            "PERIMETER_INTRUSION",
        ),
        (
            15,
            1,
            "CAM-015 [East Boundary Fence Line]",
            "test_stream",
            "sample_corridor.mp4",
            "East Perimeter Sensor Post",
            "Outer Fence",
            "PERIMETER_INTRUSION",
        ),
        (
            16,
            1,
            "CAM-016 [South Perimeter Wall 01]",
            "test_stream",
            "sample_corridor.mp4",
            "South Boundary Masonry Wall",
            "Outer Fence",
            "PERIMETER_INTRUSION",
        ),
        (
            17,
            1,
            "CAM-017 [South Perimeter Wall 02]",
            "test_stream",
            "sample_corridor.mp4",
            "South Boundary Corner Post",
            "Outer Fence",
            "PERIMETER_INTRUSION",
        ),
        (
            18,
            1,
            "CAM-018 [West Forest Border Post]",
            "test_stream",
            "sample_corridor.mp4",
            "West Tree Line Tower",
            "Outer Fence",
            "PERIMETER_INTRUSION",
        ),
        (
            19,
            1,
            "CAM-019 [Perimeter Watchtower Alpha]",
            "test_stream",
            "sample_corridor.mp4",
            "Watchtower Alpha High-Mount",
            "Watchtower",
            "PERIMETER_INTRUSION",
        ),
        (
            20,
            1,
            "CAM-020 [Perimeter Watchtower Bravo]",
            "test_stream",
            "sample_corridor.mp4",
            "Watchtower Bravo High-Mount",
            "Watchtower",
            "PERIMETER_INTRUSION",
        ),
        (
            21,
            1,
            "CAM-021 [Perimeter Watchtower Charlie]",
            "test_stream",
            "sample_corridor.mp4",
            "Watchtower Charlie High-Mount",
            "Watchtower",
            "PERIMETER_INTRUSION",
        ),
        (
            22,
            1,
            "CAM-022 [Perimeter Watchtower Delta]",
            "test_stream",
            "sample_corridor.mp4",
            "Watchtower Delta High-Mount",
            "Watchtower",
            "PERIMETER_INTRUSION",
        ),
        (
            23,
            1,
            "CAM-023 [Drainage Culvert Sensor Cam]",
            "test_stream",
            "sample_corridor.mp4",
            "Perimeter Culvert Inflow",
            "Sub-Perimeter",
            "PERIMETER_INTRUSION",
        ),
        (
            24,
            1,
            "CAM-024 [Substation Perimeter Yard]",
            "test_stream",
            "sample_corridor.mp4",
            "High-Voltage Transformer Yard",
            "Hazard Zone",
            "FIRE_SMOKE_HAZARD",
        ),
        # Sector 3: Corridors, Hallways & Walkways (Cams 25-36)
        (
            25,
            3,
            "CAM-025 [Main Concourse Hallway 1]",
            "test_stream",
            "sample_corridor.mp4",
            "Central Atrium Level 1",
            "Concourse",
            "CROWD_LOITERING",
        ),
        (
            26,
            3,
            "CAM-026 [Main Concourse Hallway 2]",
            "test_stream",
            "sample_corridor.mp4",
            "Central Atrium Level 2",
            "Concourse",
            "CROWD_LOITERING",
        ),
        (
            27,
            3,
            "CAM-027 [Academic Wing Floor 1 Hall]",
            "test_stream",
            "sample_corridor.mp4",
            "Classroom Wing 1F",
            "Academic Corridor",
            "DRESS_CODE_PPE",
        ),
        (
            28,
            3,
            "CAM-028 [Academic Wing Floor 2 Hall]",
            "test_stream",
            "sample_corridor.mp4",
            "Classroom Wing 2F",
            "Academic Corridor",
            "DRESS_CODE_PPE",
        ),
        (
            29,
            3,
            "CAM-029 [Academic Wing Floor 3 Hall]",
            "test_stream",
            "sample_corridor.mp4",
            "Classroom Wing 3F",
            "Academic Corridor",
            "DRESS_CODE_PPE",
        ),
        (
            30,
            3,
            "CAM-030 [Administration North Hall]",
            "test_stream",
            "sample_corridor.mp4",
            "Admin Building Level 1",
            "Admin Corridor",
            "FACE_ATTENDANCE",
        ),
        (
            31,
            3,
            "CAM-031 [Administration South Hall]",
            "test_stream",
            "sample_corridor.mp4",
            "Admin Building Level 2",
            "Admin Corridor",
            "FACE_ATTENDANCE",
        ),
        (
            32,
            3,
            "CAM-032 [Stairwell Central Landing 1]",
            "test_stream",
            "sample_corridor.mp4",
            "Central Emergency Stair A",
            "Stairwell",
            "CROWD_LOITERING",
        ),
        (
            33,
            3,
            "CAM-033 [Stairwell West Emergency 2]",
            "test_stream",
            "sample_corridor.mp4",
            "West Emergency Fire Stair",
            "Stairwell",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            34,
            3,
            "CAM-034 [Elevator Bank Ground Lobby]",
            "test_stream",
            "sample_corridor.mp4",
            "Elevator Bank 1F Lobby",
            "Elevator Lobby",
            "CROWD_LOITERING",
        ),
        (
            35,
            3,
            "CAM-035 [Elevator Bank Upper Lobby]",
            "test_stream",
            "sample_corridor.mp4",
            "Elevator Bank 3F Lobby",
            "Elevator Lobby",
            "CROWD_LOITERING",
        ),
        (
            36,
            3,
            "CAM-036 [Inter-Building Skybridge]",
            "test_stream",
            "sample_corridor.mp4",
            "Connecting Skybridge 2F",
            "Skybridge",
            "CROWD_LOITERING",
        ),
        # Sector 4: High-Value Vaults & Laboratories (Cams 37-48)
        (
            37,
            4,
            "CAM-037 [Defense Armory Vault Entry]",
            "test_stream",
            "sample_lab.mp4",
            "Sub-Level 1 Armory Antechamber",
            "Armory Vault",
            "WEAPON_VIOLENCE",
        ),
        (
            38,
            4,
            "CAM-038 [Armory Weapons Rack Interior]",
            "test_stream",
            "sample_lab.mp4",
            "Armory Weapon Secure Racks",
            "Classified Vault",
            "PERIMETER_INTRUSION",
        ),
        (
            39,
            4,
            "CAM-039 [Central Server Data Center 1]",
            "test_stream",
            "sample_lab.mp4",
            "IT Server Room Alpha",
            "Data Center",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            40,
            4,
            "CAM-040 [Central Server Data Center 2]",
            "test_stream",
            "sample_lab.mp4",
            "IT Server Room Bravo",
            "Data Center",
            "PERIMETER_INTRUSION",
        ),
        (
            41,
            4,
            "CAM-041 [Chemistry Research Lab 1]",
            "test_stream",
            "sample_lab.mp4",
            "Chemistry Lab Complex 101",
            "Chemical Lab",
            "DRESS_CODE_PPE",
        ),
        (
            42,
            4,
            "CAM-042 [Chemistry Research Lab 2]",
            "test_stream",
            "sample_lab.mp4",
            "Chemistry Lab Complex 102",
            "Chemical Lab",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            43,
            4,
            "CAM-043 [Biotech Cleanroom Air-Lock]",
            "test_stream",
            "sample_lab.mp4",
            "Bio-Containment Air-Lock",
            "Cleanroom",
            "DRESS_CODE_PPE",
        ),
        (
            44,
            4,
            "CAM-044 [Biotech Isolation Chamber]",
            "test_stream",
            "sample_lab.mp4",
            "BSL-3 Isolation Bay",
            "Bio Hazard",
            "PERIMETER_INTRUSION",
        ),
        (
            45,
            4,
            "CAM-045 [Classified Archive Records]",
            "test_stream",
            "sample_lab.mp4",
            "Basement Records Archive",
            "Classified Archive",
            "PERIMETER_INTRUSION",
        ),
        (
            46,
            4,
            "CAM-046 [Hazardous Materials Locker]",
            "test_stream",
            "sample_lab.mp4",
            "Hazmat Chemical Locker Bay",
            "Hazmat",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            47,
            4,
            "CAM-047 [Executive Treasury Safe]",
            "test_stream",
            "sample_lab.mp4",
            "Finance Treasury Vault",
            "Cash Vault",
            "PERIMETER_INTRUSION",
        ),
        (
            48,
            4,
            "CAM-048 [Network Operations NOC Hub]",
            "test_stream",
            "sample_lab.mp4",
            "Security Ops Center Floor",
            "NOC Hub",
            "FACE_ATTENDANCE",
        ),
        # Sector 5: Operational Workspaces & Plants (Cams 49-60)
        (
            49,
            5,
            "CAM-049 [Turbine Generator Hall A]",
            "test_stream",
            "sample_lab.mp4",
            "Power Plant Turbine Hall 1",
            "Heavy Machinery",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            50,
            5,
            "CAM-050 [Turbine Generator Hall B]",
            "test_stream",
            "sample_lab.mp4",
            "Power Plant Turbine Hall 2",
            "Heavy Machinery",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            51,
            5,
            "CAM-051 [Assembly Line Station 1]",
            "test_stream",
            "sample_corridor.mp4",
            "Manufacturing Bay Alpha",
            "Assembly Floor",
            "DRESS_CODE_PPE",
        ),
        (
            52,
            5,
            "CAM-052 [Assembly Line Station 2]",
            "test_stream",
            "sample_corridor.mp4",
            "Manufacturing Bay Bravo",
            "Assembly Floor",
            "DRESS_CODE_PPE",
        ),
        (
            53,
            5,
            "CAM-053 [Robotic Welding Cell 01]",
            "test_stream",
            "sample_lab.mp4",
            "Robotics Cell 1",
            "Welding Zone",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            54,
            5,
            "CAM-054 [Robotic Welding Cell 02]",
            "test_stream",
            "sample_lab.mp4",
            "Robotics Cell 2",
            "Welding Zone",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            55,
            5,
            "CAM-055 [Heavy Component Crane Bay]",
            "test_stream",
            "sample_corridor.mp4",
            "Overhead Gantry Crane Bay",
            "Crane Zone",
            "DRESS_CODE_PPE",
        ),
        (
            56,
            5,
            "CAM-056 [Chemical Mixing Vat Bay 1]",
            "test_stream",
            "sample_lab.mp4",
            "Industrial Reactor Floor 1",
            "Chemical Vat",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            57,
            5,
            "CAM-057 [Chemical Mixing Vat Bay 2]",
            "test_stream",
            "sample_lab.mp4",
            "Industrial Reactor Floor 2",
            "Chemical Vat",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            58,
            5,
            "CAM-058 [Quality Assurance Station]",
            "test_stream",
            "sample_corridor.mp4",
            "Final QC Inspection Bay",
            "QC Bay",
            "DRESS_CODE_PPE",
        ),
        (
            59,
            5,
            "CAM-059 [Palletizing & Dispatch Floor]",
            "test_stream",
            "sample_corridor.mp4",
            "Warehouse Dispatch Hall",
            "Packaging",
            "CROWD_LOITERING",
        ),
        (
            60,
            5,
            "CAM-060 [Plant Maintenance Workshop]",
            "test_stream",
            "sample_corridor.mp4",
            "Mechanical Tooling Shop",
            "Maintenance",
            "DRESS_CODE_PPE",
        ),
        # Sector 6: Public Plazas & Assembly Grounds (Cams 61-70)
        (
            61,
            6,
            "CAM-061 [Central Parade Ground Plaza]",
            "test_stream",
            "sample_corridor.mp4",
            "Central Parade Square",
            "Public Plaza",
            "CROWD_LOITERING",
        ),
        (
            62,
            6,
            "CAM-062 [Student Dining Hall West]",
            "test_stream",
            "sample_corridor.mp4",
            "Cafeteria Wing A",
            "Dining Hall",
            "CROWD_LOITERING",
        ),
        (
            63,
            6,
            "CAM-063 [Student Dining Hall East]",
            "test_stream",
            "sample_corridor.mp4",
            "Cafeteria Wing B",
            "Dining Hall",
            "CROWD_LOITERING",
        ),
        (
            64,
            6,
            "CAM-064 [Commercial Kitchen Range 1]",
            "test_stream",
            "sample_corridor.mp4",
            "Kitchen Hot Cooking Range",
            "Kitchen",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            65,
            6,
            "CAM-065 [Commercial Kitchen Range 2]",
            "test_stream",
            "sample_corridor.mp4",
            "Kitchen Bakery Oven Bay",
            "Kitchen",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            66,
            6,
            "CAM-066 [Outdoor Amphitheater Stage]",
            "test_stream",
            "sample_corridor.mp4",
            "Open Air Auditorium Stage",
            "Auditorium",
            "CROWD_LOITERING",
        ),
        (
            67,
            6,
            "CAM-067 [Library Reading Hall 1F]",
            "test_stream",
            "sample_corridor.mp4",
            "Main Campus Library Hall 1",
            "Library",
            "FACE_ATTENDANCE",
        ),
        (
            68,
            6,
            "CAM-068 [Library Reading Hall 2F]",
            "test_stream",
            "sample_corridor.mp4",
            "Main Campus Library Hall 2",
            "Library",
            "FACE_ATTENDANCE",
        ),
        (
            69,
            6,
            "CAM-069 [Athletics Stadium Bleachers]",
            "test_stream",
            "sample_corridor.mp4",
            "Sports Complex Grandstand",
            "Stadium",
            "WEAPON_VIOLENCE",
        ),
        (
            70,
            6,
            "CAM-070 [Indoor Sports Complex Arena]",
            "test_stream",
            "sample_corridor.mp4",
            "Indoor Basketball Arena",
            "Gymnasium",
            "WEAPON_VIOLENCE",
        ),
        # Sector 7: Logistics, Motor Pool & Parking (Cams 71-80)
        (
            71,
            7,
            "CAM-071 [Logistics Cargo Bay 01]",
            "test_stream",
            "sample_corridor.mp4",
            "Loading Dock Bay 1",
            "Cargo Bay",
            "ANPR_VEHICLES",
        ),
        (
            72,
            7,
            "CAM-072 [Logistics Cargo Bay 02]",
            "test_stream",
            "sample_corridor.mp4",
            "Loading Dock Bay 2",
            "Cargo Bay",
            "ANPR_VEHICLES",
        ),
        (
            73,
            7,
            "CAM-073 [Heavy Transport Weighbridge]",
            "test_stream",
            "sample_corridor.mp4",
            "Inbound Weigh Station",
            "Weighbridge",
            "ANPR_VEHICLES",
        ),
        (
            74,
            7,
            "CAM-074 [Fleet Vehicle Fuel Depot]",
            "test_stream",
            "sample_corridor.mp4",
            "Fuel Dispenser Station",
            "Fuel Bay",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            75,
            7,
            "CAM-075 [North Surface Parking Lot]",
            "test_stream",
            "sample_corridor.mp4",
            "North Staff Parking Lot",
            "Parking Lot",
            "ANPR_VEHICLES",
        ),
        (
            76,
            7,
            "CAM-076 [South Visitor Parking Lot]",
            "test_stream",
            "sample_corridor.mp4",
            "South Visitor Surface Lot",
            "Parking Lot",
            "ANPR_VEHICLES",
        ),
        (
            77,
            7,
            "CAM-077 [Basement Parking Level -1]",
            "test_stream",
            "sample_corridor.mp4",
            "Subterranean Parking B1",
            "Basement Park",
            "FIRE_SMOKE_HAZARD",
        ),
        (
            78,
            7,
            "CAM-078 [Basement Parking Level -2]",
            "test_stream",
            "sample_corridor.mp4",
            "Subterranean Parking B2",
            "Basement Park",
            "PERIMETER_INTRUSION",
        ),
        (
            79,
            7,
            "CAM-079 [Motor Pool Repair Depot]",
            "test_stream",
            "sample_corridor.mp4",
            "Vehicle Fleet Maintenance Garage",
            "Motor Pool",
            "DRESS_CODE_PPE",
        ),
        (
            80,
            7,
            "CAM-080 [Rear Perimeter Emergency Gate]",
            "test_stream",
            "sample_corridor.mp4",
            "Tactical Evacuation Gate Omega",
            "Emergency Gate",
            "PERIMETER_INTRUSION",
        ),
    ]

    for cam in FLEET_CAMERAS:
        cam_id, grp_id, name, src_type, src_url, loc, zone, func = cam
        cursor.execute(
            """
            INSERT OR REPLACE INTO cameras (
                id, environment_id, group_id, camera_name, source_type, source_url, location, zone, assigned_function, status, ai_enabled
            )
            VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, 'online', 1)
        """,
            (cam_id, grp_id, name, src_type, src_url, loc, zone, func),
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
