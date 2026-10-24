import http.server
import socketserver
import os
import sys
import json
import sqlite3
import hashlib
import secrets
import mimetypes
import base64
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

def get_port():
    val = os.environ.get("PORT")
    if not val and len(sys.argv) > 1 and sys.argv[1].isdigit():
        val = sys.argv[1]
    try:
        return int(val) if val else 8088
    except Exception:
        return 8088

PORT = get_port()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "sarvamangala_admin.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "assets", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==============================================================================
# Security Helpers
# ==============================================================================
def hash_password(password: str, salt: str = None) -> tuple:
    if not salt:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return pw_hash, salt

def verify_password(password: str, pw_hash: str, salt: str) -> bool:
    check_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(check_hash, pw_hash)

# ==============================================================================
# Database Initialization & Schema Migrations
# ==============================================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 1. Admin Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Member Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'active', 'suspended', 'deactivated'
        email_verified INTEGER DEFAULT 0,
        phone_verified INTEGER DEFAULT 0,
        membership_plan TEXT DEFAULT 'Free Plan',
        membership_expiry TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Sessions table
    c.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4. Profiles table
    c.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        name TEXT NOT NULL,
        gender TEXT NOT NULL,
        age INTEGER NOT NULL,
        height TEXT,
        religion TEXT DEFAULT 'Hindu',
        caste TEXT NOT NULL,
        subcaste TEXT,
        mother_tongue TEXT DEFAULT 'Tamil',
        district TEXT NOT NULL,
        city TEXT,
        address TEXT,
        education TEXT,
        occupation TEXT,
        income TEXT,
        marital_status TEXT DEFAULT 'Never Married',
        photo_url TEXT,
        rasi TEXT,
        nakshatra TEXT,
        lagnam TEXT,
        birth_date TEXT,
        birth_time TEXT,
        birth_place TEXT,
        dosham TEXT,
        jathagam_doc TEXT,
        partner_pref TEXT,
        is_approved INTEGER DEFAULT 1,
        status TEXT DEFAULT 'approved',
        payment_status TEXT DEFAULT 'Paid (₹2,000)',
        reg_date TEXT,
        compatibility INTEGER DEFAULT 90,
        notes TEXT,
        phone TEXT,
        email TEXT,
        completion_percentage INTEGER DEFAULT 85,
        is_hidden INTEGER DEFAULT 0
    )
    """)

    # Migrate profiles table if existing table lacks newer columns
    c.execute("PRAGMA table_info(profiles)")
    cols = [r[1] for r in c.fetchall()]
    new_cols = [
        ("user_id", "TEXT"),
        ("phone", "TEXT"),
        ("email", "TEXT"),
        ("completion_percentage", "INTEGER DEFAULT 85"),
        ("is_hidden", "INTEGER DEFAULT 0"),
        ("marriage_timeline", "TEXT DEFAULT 'Flexible'"),
        ("trust_badge_status", "TEXT DEFAULT 'pending'"),
        ("trust_badge_doc", "TEXT DEFAULT 'Aadhaar / Family Verification Reference'"),
        ("trust_badge_verified_at", "TEXT"),
        ("trust_badge_verified_by", "TEXT"),
        ("photo_privacy", "TEXT DEFAULT 'members_only'"),
        ("phone_privacy", "TEXT DEFAULT 'consent_only'"),
        ("horoscope_privacy", "TEXT DEFAULT 'members_only'")
    ]
    for col_name, col_type in new_cols:
        if col_name not in cols:
            try:
                c.execute(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Migration note ({col_name}): {e}")

    # 5. Registration Payments table (Mandatory GPay ₹2,000 Workflow)
    c.execute("""
    CREATE TABLE IF NOT EXISTS registration_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        registration_id TEXT UNIQUE NOT NULL,
        user_id TEXT,
        profile_id TEXT,
        applicant_name TEXT NOT NULL,
        applicant_phone TEXT NOT NULL,
        applicant_email TEXT NOT NULL,
        amount INTEGER NOT NULL DEFAULT 2000,
        payee_number TEXT NOT NULL DEFAULT '9942006877',
        payee_name TEXT NOT NULL DEFAULT 'Sarvamangala Matrimony (GPay)',
        payment_method TEXT NOT NULL DEFAULT 'Google Pay / UPI',
        txn_ref TEXT,
        status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'PAYMENT_SUBMITTED', 'PAID', 'FAILED', 'REFUNDED'
        submitted_at TIMESTAMP,
        verified_at TIMESTAMP,
        verified_by TEXT,
        notes TEXT,
        receipt_number TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 6. General Payments table
    c.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id TEXT NOT NULL,
        profile_name TEXT NOT NULL,
        payment_type TEXT NOT NULL,
        amount INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Completed',
        txn_id TEXT NOT NULL,
        method TEXT NOT NULL,
        date TEXT NOT NULL
    )
    """)

    # 7. Family Details table
    c.execute("""
    CREATE TABLE IF NOT EXISTS family_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id TEXT UNIQUE NOT NULL,
        father_name TEXT,
        father_occupation TEXT,
        mother_name TEXT,
        mother_occupation TEXT,
        brothers INTEGER DEFAULT 0,
        sisters INTEGER DEFAULT 0,
        family_type TEXT DEFAULT 'Nuclear',
        family_values TEXT DEFAULT 'Traditional',
        native_place TEXT,
        family_wealth TEXT
    )
    """)

    # 8. Partner Preferences table
    c.execute("""
    CREATE TABLE IF NOT EXISTS partner_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id TEXT UNIQUE NOT NULL,
        age_from INTEGER DEFAULT 21,
        age_to INTEGER DEFAULT 35,
        height_from TEXT,
        height_to TEXT,
        marital_status TEXT DEFAULT 'Never Married',
        caste TEXT DEFAULT 'Any',
        education TEXT DEFAULT 'Any',
        occupation TEXT DEFAULT 'Any',
        district TEXT DEFAULT 'Any',
        dosham_pref TEXT DEFAULT 'No Dosham'
    )
    """)

    # 9. Interests table
    c.execute("""
    CREATE TABLE IF NOT EXISTS interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id TEXT NOT NULL,
        receiver_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'accepted', 'declined', 'withdrawn'
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(sender_id, receiver_id)
    )
    """)

    # 10. Shortlists table
    c.execute("""
    CREATE TABLE IF NOT EXISTS shortlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        profile_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, profile_id)
    )
    """)

    # 11. Contact Requests table
    c.execute("""
    CREATE TABLE IF NOT EXISTS contact_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        requester_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(requester_id, target_id)
    )
    """)

    # 12. Notifications table
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'info', -- 'interest', 'contact', 'verification', 'system'
        is_read INTEGER DEFAULT 0,
        link TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 13. Membership Plans table
    c.execute("""
    CREATE TABLE IF NOT EXISTS membership_plans (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        validity_days INTEGER NOT NULL,
        contact_limit INTEGER NOT NULL,
        features TEXT NOT NULL,
        is_popular INTEGER DEFAULT 0
    )
    """)

    # 13b. User Memberships tracking table
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        plan_id TEXT NOT NULL,
        plan_name TEXT NOT NULL,
        price INTEGER NOT NULL,
        validity_days INTEGER NOT NULL,
        status TEXT NOT NULL, -- 'active', 'pending_verification', 'expired', 'rejected'
        start_date TEXT,
        expiry_date TEXT,
        payment_method TEXT,
        txn_ref TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 14. Profile Reports table
    c.execute("""
    CREATE TABLE IF NOT EXISTS profile_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_id TEXT,
        reported_profile_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        details TEXT,
        status TEXT DEFAULT 'pending', -- 'pending', 'reviewed', 'dismissed'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 15. Success Stories & Testimonials table
    c.execute("""
    CREATE TABLE IF NOT EXISTS testimonials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        couple_name TEXT NOT NULL,
        district TEXT NOT NULL,
        marriage_date TEXT NOT NULL,
        story TEXT NOT NULL,
        photo_url TEXT,
        rating INTEGER DEFAULT 5,
        is_approved INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 16. Admin Activity Logs table and Phase 1 & 2 schemas
    c.executescript("""
    CREATE TABLE IF NOT EXISTS secret_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_profile_id TEXT NOT NULL,
        target_profile_id TEXT NOT NULL,
        is_mutual INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(sender_profile_id, target_profile_id)
    );

    CREATE TABLE IF NOT EXISTS ice_breakers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id TEXT NOT NULL,
        receiver_id TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT,
        status TEXT DEFAULT 'sent', -- 'sent', 'answered', 'declined'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        answered_at TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS horoscope_poruthams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        boy_rasi TEXT NOT NULL,
        boy_nakshatra TEXT NOT NULL,
        girl_rasi TEXT NOT NULL,
        girl_nakshatra TEXT NOT NULL,
        total_score INTEGER DEFAULT 8,
        compatibility_status TEXT DEFAULT 'Uthama Porutham (Excellent)',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS local_connect (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id TEXT UNIQUE NOT NULL,
        latitude REAL,
        longitude REAL,
        area_name TEXT,
        district TEXT DEFAULT 'Kanchipuram',
        radius_km INTEGER DEFAULT 25,
        is_enabled INTEGER DEFAULT 0,
        consent_timestamp TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS quick_intros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id TEXT UNIQUE NOT NULL,
        video_url TEXT NOT NULL,
        duration_seconds INTEGER DEFAULT 30,
        thumbnail_url TEXT,
        status TEXT DEFAULT 'pending_review',
        visibility TEXT DEFAULT 'members_only',
        reviewed_by TEXT,
        reviewed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS call_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caller_id TEXT NOT NULL,
        receiver_id TEXT NOT NULL,
        call_type TEXT DEFAULT 'audio',
        channel_name TEXT NOT NULL,
        status TEXT DEFAULT 'requested',
        duration_seconds INTEGER DEFAULT 0,
        consent_caller INTEGER DEFAULT 1,
        consent_receiver INTEGER DEFAULT 0,
        started_at TIMESTAMP,
        ended_at TIMESTAMP,
        is_reported INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_email TEXT NOT NULL,
        action TEXT NOT NULL,
        target_id TEXT,
        details TEXT,
        ip_address TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 17. Family Enquiries table
    c.execute("""
    CREATE TABLE IF NOT EXISTS enquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        subject TEXT,
        message TEXT,
        district TEXT DEFAULT 'Kanchipuram',
        status TEXT DEFAULT 'New',
        date TEXT NOT NULL
    )
    """)
    # Check if enquiries has email and subject
    c.execute("PRAGMA table_info(enquiries)")
    eq_cols = [r[1] for r in c.fetchall()]
    if "email" not in eq_cols:
        c.execute("ALTER TABLE enquiries ADD COLUMN email TEXT")
    if "subject" not in eq_cols:
        c.execute("ALTER TABLE enquiries ADD COLUMN subject TEXT")

    # ==========================================================================
    # Seed Data
    # ==========================================================================
    # Seed Admin User if not exists
    c.execute("SELECT id FROM admin_users WHERE email = ?", ("admin@sarvamangala.com",))
    if not c.fetchone():
        pw_hash, salt = hash_password("KanchiMangala@2026")
        c.execute("""
        INSERT INTO admin_users (email, name, password_hash, salt, role)
        VALUES (?, ?, ?, ?, ?)
        """, ("admin@sarvamangala.com", "Temple City Administrator", pw_hash, salt, "admin"))

    # Seed Membership Plans (Exact 3 Plans as requested)
    c.execute("DELETE FROM membership_plans")
    plans = [
        ("free", "Free Plan", 0, 30, 2, json.dumps([
            "Create and edit a matrimonial profile",
            "Upload a profile photo",
            "Search bride and groom profiles",
            "View basic profile details"
        ]), 0),
        ("gold", "Gold Plan", 2000, 180, 35, json.dumps([
            "All Free features",
            "Shortlist profiles",
            "Send interest requests",
            "Access eligible contact details with privacy permissions",
            "Priority profile visibility"
        ]), 1),
        ("diamond", "Diamond Plan", 3000, 365, 80, json.dumps([
            "All Gold features",
            "Advanced match filters",
            "Enhanced profile visibility",
            "Higher shortlist and interest-request limits",
            "Priority support",
            "Matchmaking assistance if available"
        ]), 0)
    ]
    c.executemany("""
    INSERT INTO membership_plans (id, name, price, validity_days, contact_limit, features, is_popular)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, plans)

    # Seed Testimonials / Success Stories if empty
    c.execute("SELECT COUNT(*) FROM testimonials")
    if c.fetchone()[0] == 0:
        testimonials = [
            ("Sundararajan & Revathi", "Kanchipuram", "March 2026", "We found our alliance through Sarvamangala Matrimony within two months of registration. The 10 Porutham verification and direct family assistance from their Vallal Pachaiyappan Street office made our families completely confident. Today, we are happily married!", "https://images.unsplash.com/photo-1583939003579-730e3918a45a?auto=format&fit=crop&w=600&q=80", 5, 1),
            ("Dr. Aravindhan & Dr. Sneha", "Madurai & Chennai", "January 2026", "Being doctors with demanding schedules, finding time for matchmaking was hard. Sarvamangala Matrimony presented verified, dignified medical alliances with accurate Jathagam. The privacy protection was exemplary.", "https://images.unsplash.com/photo-1511285560929-80b456fea0bc?auto=format&fit=crop&w=600&q=80", 5, 1),
            ("Muthukumar & Radhika", "Vellore", "November 2025", "Our parents appreciated the transparent fixed fee structure — no hidden subscriptions, just pure traditional respect. Both our families met at the Kanchipuram office and finalised the wedding smoothly.", "https://images.unsplash.com/photo-1609154767012-331529e7d73b?auto=format&fit=crop&w=600&q=80", 5, 1),
            ("Karthikeyan & Deepalakshmi", "Chengalpattu", "September 2025", "The Priya Matching compatibility showed a 94% score, and when our family astrologer inspected the horoscopes, every single Porutham matched perfectly. Highly recommended for all Tamil Hindu families.", "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=600&q=80", 5, 1)
        ]
        c.executemany("""
        INSERT INTO testimonials (couple_name, district, marriage_date, story, photo_url, rating, is_approved)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, testimonials)

    # Seed a Demo Active Member User if none exists
    c.execute("SELECT id FROM users WHERE email = ?", ("demo@sarvamangala.com",))
    if not c.fetchone():
        pw_hash, salt = hash_password("Member@2026")
        demo_user_id = "USR-2026-9214"
        c.execute("""
        INSERT INTO users (id, email, phone, name, password_hash, salt, role, status, email_verified, phone_verified, membership_plan)
        VALUES (?, ?, ?, ?, ?, ?, 'user', 'active', 1, 1, 'Gold Vivaham')
        """, (demo_user_id, "demo@sarvamangala.com", "9842109214", "Priya S.", pw_hash, salt))
        
        # Link to profile SM-2026-9214
        c.execute("UPDATE profiles SET user_id = ?, phone = ?, email = ? WHERE id = 'SM-2026-9214'",
                  (demo_user_id, "9842109214", "demo@sarvamangala.com"))

    # Seed demo notifications
    c.execute("SELECT COUNT(*) FROM notifications")
    if c.fetchone()[0] == 0:
        c.execute("""
        INSERT INTO notifications (user_id, title, message, type, is_read, link)
        VALUES 
        ('USR-2026-9214', 'Welcome to Sarvamangala Matrimony', 'Your ₹2,000 registration fee has been verified and your profile is active.', 'verification', 0, '#dashboard'),
        ('USR-2026-9214', 'New Match Found', 'Vignesh M. (SM-2026-7310) matches your partner preferences with 94% compatibility.', 'interest', 0, '#matches-section')
        """)

    conn.commit()
    conn.close()

# Helper: Log activity
def log_activity(admin_email: str, action: str, target_id: str, details: str, ip: str = "127.0.0.1"):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
        INSERT INTO activity_logs (admin_email, action, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?)
        """, (admin_email, action, target_id, details, ip))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Log activity error: {e}")

# Helper: Verify Session Token (Admin)
def verify_admin_session(token: str) -> dict:
    if not token:
        return None
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
        SELECT s.user_id, s.email, s.role, s.expires_at, a.name
        FROM sessions s
        LEFT JOIN admin_users a ON (s.email = a.email)
        WHERE s.token = ? AND s.role = 'admin'
        """, (token,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        user_id, email, role, expires_at, name = row
        if datetime.fromisoformat(expires_at) < datetime.now():
            return None
        return {"user_id": user_id, "email": email, "role": role, "name": name or "Temple City Administrator"}
    except Exception as e:
        print(f"Session verify error: {e}")
        return None

# Helper: Verify Session Token (User or Admin)
def verify_user_session(token: str) -> dict:
    if not token:
        return None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
        SELECT s.user_id, s.email, s.role, s.expires_at, u.name, u.phone, u.status as user_status, u.membership_plan, u.membership_expiry
        FROM sessions s
        LEFT JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
        """, (token,))
        row = c.fetchone()
        if not row:
            conn.close()
            return None
        
        row_dict = dict(row)
        if datetime.fromisoformat(row_dict["expires_at"]) < datetime.now():
            conn.close()
            return None

        # Fetch linked profile if any
        c.execute("SELECT id as profile_id, name, gender, age, caste, district, photo_url, is_approved, completion_percentage FROM profiles WHERE user_id = ? OR email = ? OR id = ?",
                  (row_dict["user_id"], row_dict["email"], row_dict["user_id"]))
        prof = c.fetchone()
        if prof:
            row_dict["profile"] = dict(prof)
        else:
            row_dict["profile"] = None

        conn.close()
        return row_dict
    except Exception as e:
        print(f"User session verify error: {e}")
        return None

# ==============================================================================
# Phase 1 Priority Feature Helpers
# ==============================================================================
PRESET_ICE_BREAKERS = [
    "What qualities are most important to you in a life partner?",
    "What are your interests and hobbies outside work?",
    "What are your expectations for family life and traditional values?",
    "Where would you prefer to settle after marriage?",
    "How do you enjoy celebrating family festivals and auspicious occasions?"
]

TIER_LIMITS = {
    "free": {"shortlist": 5, "interests": 2, "icebreaker": 2, "secret_likes": 5},
    "gold": {"shortlist": 35, "interests": 35, "icebreaker": 15, "secret_likes": 35},
    "diamond": {"shortlist": 80, "interests": 80, "icebreaker": 9999, "secret_likes": 9999}
}

def generate_unique_profile_id(cursor, year=2026) -> str:
    cursor.execute("SELECT id FROM profiles WHERE id LIKE ? ORDER BY id DESC LIMIT 1", (f"SMK-{year}-%",))
    row = cursor.fetchone()
    if row and row[0]:
        try:
            curr_seq = int(row[0].split("-")[-1])
            seq = curr_seq + 1
        except Exception:
            seq = 1
    else:
        cursor.execute("SELECT COUNT(*) FROM profiles")
        seq = cursor.fetchone()[0] + 1

    while True:
        pid = f"SMK-{year}-{seq:06d}"
        cursor.execute("SELECT id FROM profiles WHERE id = ?", (pid,))
        if not cursor.fetchone():
            return pid
        seq += 1

def check_tier_limit(cursor, user_id: str, plan_name: str, action: str) -> tuple[bool, str]:
    tier = "free"
    p_lower = (plan_name or "").lower()
    if "diamond" in p_lower:
        tier = "diamond"
    elif "gold" in p_lower:
        tier = "gold"

    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    limit_val = limits.get(action, 9999)

    if action == "shortlist":
        cursor.execute("SELECT COUNT(*) FROM shortlists WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        if count >= limit_val:
            return False, f"Shortlist limit of {limit_val} reached for {tier.capitalize()} Plan. Upgrade to save more profiles."
    elif action == "interests":
        cursor.execute("SELECT COUNT(*) FROM interests WHERE sender_id IN (SELECT id FROM profiles WHERE user_id = ?)", (user_id,))
        count = cursor.fetchone()[0]
        if count >= limit_val:
            return False, f"Interest request limit of {limit_val} reached for {tier.capitalize()} Plan. Upgrade to connect with more profiles."
    elif action == "icebreaker":
        cursor.execute("SELECT COUNT(*) FROM ice_breakers WHERE sender_id IN (SELECT id FROM profiles WHERE user_id = ?)", (user_id,))
        count = cursor.fetchone()[0]
        if count >= limit_val:
            return False, f"Ice Breaker question limit of {limit_val} reached for {tier.capitalize()} Plan. Upgrade for more ice breakers."
    elif action == "secret_likes":
        cursor.execute("SELECT COUNT(*) FROM secret_likes WHERE sender_profile_id IN (SELECT id FROM profiles WHERE user_id = ?)", (user_id,))
        count = cursor.fetchone()[0]
        if count >= limit_val:
            return False, f"Secret Like limit of {limit_val} reached for {tier.capitalize()} Plan. Upgrade to Gold or Diamond."

    return True, ""

def apply_privacy_mask(p: dict, viewer_user: dict, cursor) -> dict:
    res = dict(p)
    my_uid = viewer_user["user_id"] if viewer_user else None
    my_pid = viewer_user.get("profile", {}).get("profile_id", my_uid) if viewer_user else None
    is_self = viewer_user and (p.get("user_id") == my_uid or p.get("id") == my_pid)
    is_admin = viewer_user and viewer_user.get("role") == "admin"

    if is_admin:
        res["can_see_contact"] = True
        res["photo_masked"] = False
        return res

    if is_self:
        res["can_see_contact"] = True
        res["photo_masked"] = False
        return res

    # Never leak confidential trust badge identity documents to visitors/members
    res.pop("trust_badge_doc", None)

    photo_privacy = p.get("photo_privacy") or "members_only"
    phone_privacy = p.get("phone_privacy") or "consent_only"

    has_contact_approval = False
    if viewer_user and my_pid and cursor:
        cursor.execute("""
        SELECT status FROM contact_requests 
        WHERE (requester_id = ? AND target_id = ? AND status = 'approved')
           OR (requester_id = ? AND target_id = ? AND status = 'approved')
        """, (my_pid, p["id"], p["id"], my_pid))
        if cursor.fetchone():
            has_contact_approval = True

    # Photo Privacy
    if not viewer_user:
        if photo_privacy != "everyone":
            res["photo_masked"] = True
            res["photo_url"] = "assets/avatar-placeholder.png"
        else:
            res["photo_masked"] = False
    else:
        if photo_privacy == "approved_contacts_only" and not has_contact_approval:
            res["photo_masked"] = True
            res["photo_url"] = "assets/avatar-placeholder.png"
        elif photo_privacy == "hidden":
            res["photo_masked"] = True
            res["photo_url"] = "assets/avatar-placeholder.png"
        else:
            res["photo_masked"] = False

    # Phone Privacy
    if not viewer_user:
        res["phone"] = "🔒 Verified via Kanchipuram Office (Login Required)"
        res["email"] = "🔒 Protected"
        res["address"] = f"{res.get('city', '')}, {res.get('district', '')}"
        res["can_see_contact"] = False
    else:
        if phone_privacy == "hidden":
            res["phone"] = "🔒 Private"
            res["email"] = "🔒 Private"
            res["can_see_contact"] = False
        elif phone_privacy == "consent_only":
            if has_contact_approval:
                res["can_see_contact"] = True
            else:
                res["phone"] = "🔒 Contact Request Required"
                res["email"] = "🔒 Contact Request Required"
                res["can_see_contact"] = False
        elif phone_privacy == "members_only":
            res["can_see_contact"] = True

    return res

# ==============================================================================
# Custom Request Handler
# ==============================================================================
class MatrimonyServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def extract_token(self) -> str:
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()
        cookie_header = self.headers.get("Cookie", "")
        is_admin_req = "/admin" in self.path or "/sm-admin" in self.path
        if is_admin_req:
            for item in cookie_header.split(";"):
                item = item.strip()
                if item.startswith("sm_admin_session="):
                    return item.split("=", 1)[1].strip()
            return ""
        for item in cookie_header.split(";"):
            item = item.strip()
            if item.startswith("sm_session="):
                return item.split("=", 1)[1].strip()
            if item.startswith("sm_admin_session="):
                return item.split("=", 1)[1].strip()
        return ""

    def send_json(self, data, status=200, extra_headers=None):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def send_unauthorized(self, message="Authentication required"):
        self.send_json({"error": message, "authenticated": False}, status=401)

    def send_forbidden(self, message="Access Denied"):
        self.send_json({"error": message, "authenticated": False}, status=403)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    # --------------------------------------------------------------------------
    # GET Handling
    # --------------------------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        clean_path = parsed.path.rstrip("/")
        if clean_path == "":
            clean_path = "/"

        # 1. Private Admin Route: /sm-admin, /sm-admin/dashboard, etc.
        if clean_path in ["/sm-admin", "/sm-admin/dashboard"] or clean_path.startswith("/sm-admin/"):
            admin_file = os.path.join(BASE_DIR, "sm-admin", "index.html")
            if os.path.exists(admin_file):
                with open(admin_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive, nosnippet")
                self.end_headers()
                self.wfile.write(content)
                return

        # 2. Dedicated Authentication Pages (/login and /register)
        if clean_path in ["/login", "/login.html"]:
            login_file = os.path.join(BASE_DIR, "login.html")
            if os.path.exists(login_file):
                with open(login_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        if clean_path in ["/register", "/register.html"]:
            register_file = os.path.join(BASE_DIR, "register.html")
            if os.path.exists(register_file):
                with open(register_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        if clean_path in ["/membership-details", "/membership-details.html"]:
            mem_file = os.path.join(BASE_DIR, "membership-details.html")
            if os.path.exists(mem_file):
                with open(mem_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # 3. Public / SPA Routes (/matches, /dashboard, /plans, /about, /contact, /profile/...)
        spa_routes = ["/matches", "/dashboard", "/plans", "/about", "/contact",
                      "/interests", "/shortlist", "/contact-requests", "/notifications", "/settings", "/profile"]
        if clean_path in spa_routes or clean_path.startswith("/profile/"):
            index_file = os.path.join(BASE_DIR, "index.html")
            if os.path.exists(index_file):
                with open(index_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # 3. Member / Auth Endpoints
        if clean_path == "/api/auth/me":
            token = self.extract_token()
            user = verify_user_session(token)
            if user:
                self.send_json({"authenticated": True, "user": user})
            else:
                self.send_json({"authenticated": False, "user": None})
            return

        elif clean_path == "/api/auth/payment-status":
            qs = parse_qs(parsed.query)
            reg_id = qs.get("reg_id", [""])[0]
            if not reg_id:
                self.send_json({"error": "Registration ID required"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM registration_payments WHERE registration_id = ?", (reg_id,))
            row = c.fetchone()
            conn.close()

            if not row:
                self.send_json({"error": "Registration record not found"}, status=404)
                return

            p = dict(row)
            self.send_json({
                "registration_id": p["registration_id"],
                "status": p["status"],
                "amount": p["amount"],
                "payee_number": p["payee_number"],
                "payee_name": p["payee_name"],
                "txn_ref": p["txn_ref"],
                "applicant_name": p["applicant_name"],
                "receipt_number": p["receipt_number"],
                "verified_at": p["verified_at"]
            })
            return

        # 4. Search & Matches Endpoint (Approved profiles only)
        elif clean_path == "/api/matches":
            qs = parse_qs(parsed.query)
            gender = qs.get("gender", ["all"])[0].lower()
            age_min = int(qs.get("age_min", [18])[0])
            age_max = int(qs.get("age_max", [70])[0])
            district = qs.get("district", ["all"])[0]
            caste = qs.get("caste", ["all"])[0]
            education = qs.get("education", ["all"])[0]
            timeline = qs.get("timeline", ["all"])[0].strip()
            search = qs.get("q", [""])[0]
            sort_by = qs.get("sort", ["newest"])[0]
            page = max(1, int(qs.get("page", [1])[0]))
            limit = min(50, max(1, int(qs.get("limit", [12])[0])))
            offset = (page - 1) * limit

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            query = "SELECT * FROM profiles WHERE is_approved = 1 AND is_hidden = 0"
            params = []

            if gender in ["female", "bride"]:
                query += " AND LOWER(gender) = 'female'"
            elif gender in ["male", "groom"]:
                query += " AND LOWER(gender) = 'male'"

            query += " AND age >= ? AND age <= ?"
            params.extend([age_min, age_max])

            if district != "all" and district.strip():
                query += " AND LOWER(district) = LOWER(?)"
                params.append(district.strip())

            if caste != "all" and caste.strip():
                query += " AND LOWER(caste) LIKE LOWER(?)"
                params.append(f"%{caste.strip()}%")

            if education != "all" and education.strip():
                query += " AND LOWER(education) LIKE LOWER(?)"
                params.append(f"%{education.strip()}%")

            if timeline != "all" and timeline:
                query += " AND LOWER(marriage_timeline) = LOWER(?)"
                params.append(timeline)

            if search.strip():
                query += " AND (LOWER(name) LIKE LOWER(?) OR LOWER(caste) LIKE LOWER(?) OR LOWER(district) LIKE LOWER(?) OR LOWER(occupation) LIKE LOWER(?) OR LOWER(id) LIKE LOWER(?))"
                s = f"%{search.strip()}%"
                params.extend([s, s, s, s, s])

            count_query = query.replace("SELECT *", "SELECT COUNT(*)", 1)
            c.execute(count_query, params)
            total_records = c.fetchone()[0]

            if sort_by == "compatibility":
                query += " ORDER BY compatibility DESC, reg_date DESC"
            elif sort_by == "age_asc":
                query += " ORDER BY age ASC"
            elif sort_by == "age_desc":
                query += " ORDER BY age DESC"
            else:
                query += " ORDER BY reg_date DESC, id DESC"

            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            c.execute(query, params)
            raw_profiles = [dict(r) for r in c.fetchall()]

            # Fetch user session for privacy & interaction states
            token = self.extract_token()
            user = verify_user_session(token)

            shortlisted_ids = set()
            sent_interests = {}
            secret_liked_ids = {}
            if user:
                uid = user["user_id"]
                my_pid = user.get("profile", {}).get("profile_id", uid)
                c.execute("SELECT profile_id FROM shortlists WHERE user_id = ?", (uid,))
                shortlisted_ids = set(r[0] for r in c.fetchall())
                c.execute("SELECT receiver_id, status FROM interests WHERE sender_id = ?", (my_pid,))
                sent_interests = dict(c.fetchall())
                c.execute("SELECT target_profile_id, is_mutual FROM secret_likes WHERE sender_profile_id = ?", (my_pid,))
                secret_liked_ids = {r[0]: bool(r[1]) for r in c.fetchall()}

            profiles = []
            for raw_p in raw_profiles:
                p = apply_privacy_mask(raw_p, user, c)
                p["is_shortlisted"] = p["id"] in shortlisted_ids
                p["interest_status"] = sent_interests.get(p["id"], None)
                p["is_liked"] = p["id"] in secret_liked_ids
                p["is_mutual"] = secret_liked_ids.get(p["id"], False)
                profiles.append(p)

            conn.close()
            self.send_json({
                "profiles": profiles,
                "total": total_records,
                "page": page,
                "limit": limit,
                "total_pages": (total_records + limit - 1) // limit
            })
            return

        # 5. Profile Details Endpoint
        elif clean_path.startswith("/api/profile/"):
            pid = clean_path.split("/")[-1]
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM profiles WHERE id = ?", (pid,))
            row = c.fetchone()
            if not row:
                conn.close()
                self.send_json({"error": "Profile not found"}, status=404)
                return

            raw_profile = dict(row)
            # Fetch family details
            c.execute("SELECT * FROM family_details WHERE profile_id = ?", (pid,))
            fam = c.fetchone()
            raw_profile["family"] = dict(fam) if fam else None

            # Fetch partner preferences
            c.execute("SELECT * FROM partner_preferences WHERE profile_id = ?", (pid,))
            pref = c.fetchone()
            raw_profile["preferences"] = dict(pref) if pref else None

            token = self.extract_token()
            user = verify_user_session(token)
            profile = apply_privacy_mask(raw_profile, user, c)

            # Check interaction status
            profile["is_shortlisted"] = False
            profile["interest_status"] = None
            profile["is_liked"] = False
            profile["is_mutual"] = False

            if user:
                my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
                c.execute("SELECT id FROM shortlists WHERE user_id = ? AND profile_id = ?", (user["user_id"], pid))
                if c.fetchone():
                    profile["is_shortlisted"] = True
                c.execute("SELECT status FROM interests WHERE sender_id = ? AND receiver_id = ?", (my_pid, pid))
                int_row = c.fetchone()
                if int_row:
                    profile["interest_status"] = int_row[0]
                c.execute("SELECT is_mutual FROM secret_likes WHERE sender_profile_id = ? AND target_profile_id = ?", (my_pid, pid))
                like_row = c.fetchone()
                if like_row:
                    profile["is_liked"] = True
                    profile["is_mutual"] = bool(like_row[0])

            conn.close()
            self.send_json({"profile": profile, "can_see_contact": profile.get("can_see_contact", False)})
            return

        # 6. User Interests Endpoint
        elif clean_path == "/api/interests":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Sent interests
            c.execute("""
            SELECT i.id, i.status, i.message, i.created_at, p.id as profile_id, p.name, p.age, p.caste, p.district, p.occupation, p.photo_url
            FROM interests i
            JOIN profiles p ON i.receiver_id = p.id
            WHERE i.sender_id = ?
            ORDER BY i.created_at DESC
            """, (my_pid,))
            sent = [dict(r) for r in c.fetchall()]

            # Received interests
            c.execute("""
            SELECT i.id, i.status, i.message, i.created_at, p.id as profile_id, p.name, p.age, p.caste, p.district, p.occupation, p.photo_url
            FROM interests i
            JOIN profiles p ON i.sender_id = p.id
            WHERE i.receiver_id = ?
            ORDER BY i.created_at DESC
            """, (my_pid,))
            received = [dict(r) for r in c.fetchall()]

            conn.close()
            self.send_json({"sent": sent, "received": received})
            return

                # 6b. Secret Likes: Mutual Matches Endpoint
        elif clean_path == "/api/secret-likes/mutual":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""
            SELECT sl.id as match_id, sl.created_at as mutual_since, p.*
            FROM secret_likes sl
            JOIN profiles p ON sl.target_profile_id = p.id
            WHERE sl.sender_profile_id = ? AND sl.is_mutual = 1
            ORDER BY sl.created_at DESC
            """, (my_pid,))
            mutual_matches = []
            for r in c.fetchall():
                d = dict(r)
                d["profile_id"] = d["id"]
                mutual_matches.append(apply_privacy_mask(d, user, c))
            conn.close()
            self.send_json({"mutual_matches": mutual_matches})
            return

        # 6c. Ice Breaker Questions: Presets, Received & Sent
        elif clean_path == "/api/icebreakers":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Received icebreakers
            c.execute("""
            SELECT ib.id, ib.question, ib.answer, ib.status, ib.created_at, ib.answered_at,
                   p.id as sender_profile_id, p.name as sender_name, p.age as sender_age, p.district as sender_district, p.photo_url as sender_photo
            FROM ice_breakers ib
            JOIN profiles p ON ib.sender_id = p.id
            WHERE ib.receiver_id = ?
            ORDER BY ib.created_at DESC
            """, (my_pid,))
            received = [dict(r) for r in c.fetchall()]

            # Sent icebreakers
            c.execute("""
            SELECT ib.id, ib.question, ib.answer, ib.status, ib.created_at, ib.answered_at,
                   p.id as receiver_profile_id, p.name as receiver_name, p.age as receiver_age, p.district as receiver_district, p.photo_url as receiver_photo
            FROM ice_breakers ib
            JOIN profiles p ON ib.receiver_id = p.id
            WHERE ib.sender_id = ?
            ORDER BY ib.created_at DESC
            """, (my_pid,))
            sent = [dict(r) for r in c.fetchall()]

            conn.close()
            self.send_json({
                "presets": PRESET_ICE_BREAKERS,
                "received": received,
                "sent": sent
            })
            return

        # 6d. Privacy Settings: Get
        elif clean_path == "/api/settings/privacy":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT photo_privacy, phone_privacy, horoscope_privacy, trust_badge_status, trust_badge_doc FROM profiles WHERE id = ? OR user_id = ?", (my_pid, user["user_id"]))
            row = c.fetchone()
            conn.close()
            if not row:
                default_priv = {"photo_privacy": "everyone", "phone_privacy": "consent_only", "horoscope_privacy": "open", "trust_badge_status": "unverified"}
                self.send_json({"privacy": default_priv, **default_priv})
                return
            row_data = dict(row)
            self.send_json({"privacy": row_data, **row_data})
            return

        # 7. User Shortlist Endpoint
        elif clean_path == "/api/shortlist":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""
            SELECT s.id as shortlist_id, s.created_at, p.*
            FROM shortlists s
            JOIN profiles p ON s.profile_id = p.id
            WHERE s.user_id = ?
            ORDER BY s.created_at DESC
            """, (user["user_id"],))
            items = []
            for r in c.fetchall():
                p = dict(r)
                p["phone"] = "🔒 Verified via Kanchipuram Office"
                items.append(p)
            conn.close()
            self.send_json({"shortlist": items})
            return

        # 8. User Contact Requests Endpoint
        elif clean_path == "/api/contact-requests":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute("""
            SELECT cr.id, cr.status, cr.message, cr.created_at, p.id as profile_id, p.name, p.age, p.district, p.photo_url,
                   CASE WHEN cr.status = 'approved' THEN p.phone ELSE '🔒 Approval Required' END as contact_phone
            FROM contact_requests cr
            JOIN profiles p ON cr.target_id = p.id
            WHERE cr.requester_id = ?
            ORDER BY cr.created_at DESC
            """, (my_pid,))
            outgoing = [dict(r) for r in c.fetchall()]

            c.execute("""
            SELECT cr.id, cr.status, cr.message, cr.created_at, p.id as profile_id, p.name, p.age, p.district, p.photo_url,
                   p.phone as applicant_phone
            FROM contact_requests cr
            JOIN profiles p ON cr.requester_id = p.id
            WHERE cr.target_id = ?
            ORDER BY cr.created_at DESC
            """, (my_pid,))
            incoming = [dict(r) for r in c.fetchall()]

            conn.close()
            self.send_json({"outgoing": outgoing, "incoming": incoming})
            return

        # 9. User Notifications Endpoint
        elif clean_path == "/api/notifications":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", (user["user_id"],))
            notifs = [dict(r) for r in c.fetchall()]
            conn.close()
            self.send_json({"notifications": notifs})
            return

        # 10. Public Testimonials & Plans
        elif clean_path == "/api/public/testimonials":
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM testimonials WHERE is_approved = 1 ORDER BY id DESC")
            stories = [dict(r) for r in c.fetchall()]
            conn.close()
            self.send_json({"testimonials": stories})
            return

        elif clean_path in ["/api/public/plans", "/api/plans"]:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM membership_plans ORDER BY price ASC")
            plans = []
            for r in c.fetchall():
                p = dict(r)
                p["features"] = json.loads(p["features"]) if isinstance(p["features"], str) else p["features"]
                plans.append(p)
            conn.close()
            self.send_json({"plans": plans})
            return

        elif clean_path == "/api/membership/current":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_json({"authenticated": False, "user": None, "membership": None})
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""
            SELECT * FROM user_memberships
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 1
            """, (user["user_id"],))
            mem_row = c.fetchone()
            latest_mem = dict(mem_row) if mem_row else None

            c.execute("SELECT * FROM membership_plans ORDER BY price ASC")
            plans = []
            for r in c.fetchall():
                p = dict(r)
                p["features"] = json.loads(p["features"]) if isinstance(p["features"], str) else p["features"]
                plans.append(p)
            conn.close()

            plan_name = user.get("membership_plan") or "Free Plan"
            expiry_date = user.get("membership_expiry")
            status = "active"
            if latest_mem:
                status = latest_mem.get("status", "active")

            self.send_json({
                "authenticated": True,
                "user": {
                    "id": user["user_id"],
                    "name": user["name"],
                    "email": user["email"],
                    "phone": user["phone"],
                    "membership_plan": plan_name,
                    "membership_expiry": expiry_date,
                    "membership_status": status
                },
                "current_membership": latest_mem,
                "plans": plans
            })
            return

        # 11. Admin Endpoints
        elif clean_path.startswith("/api/admin/"):
            token = self.extract_token()
            user = verify_admin_session(token)

            if clean_path == "/api/admin/session":
                if user:
                    self.send_json({"authenticated": True, "user": user})
                else:
                    self.send_json({"authenticated": False, "user": None})
                return

            if not user:
                self.send_forbidden("Admin authorization required")
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Kanchi Silk Trust Badges Queue
            if clean_path == "/api/admin/trust-badges":
                c.execute("""
                SELECT id, name, gender, age, district, phone, trust_badge_status, trust_badge_doc, trust_badge_verified_at, trust_badge_verified_by
                FROM profiles
                ORDER BY CASE WHEN trust_badge_status = 'pending' THEN 0 ELSE 1 END, id ASC
                """)
                badges = [dict(r) for r in c.fetchall()]
                conn.close()
                self.send_json({"badges": badges})
                return

            # Dashboard stats
            if clean_path == "/api/admin/stats":
                c.execute("SELECT COUNT(*) FROM profiles")
                total_members = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM profiles WHERE LOWER(gender) = 'female'")
                brides_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM profiles WHERE LOWER(gender) = 'male'")
                grooms_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM profiles WHERE status = 'pending' OR is_approved = 0")
                pending_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM profiles WHERE status = 'approved' AND is_approved = 1")
                approved_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM profiles WHERE status = 'rejected'")
                rejected_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM registration_payments WHERE status = 'PAYMENT_SUBMITTED'")
                pending_payments = c.fetchone()[0]
                c.execute("SELECT SUM(amount) FROM payments WHERE payment_type LIKE '%Registration%'")
                reg_fees = c.fetchone()[0] or 0
                c.execute("SELECT SUM(amount) FROM payments WHERE payment_type LIKE '%Finalisation%'")
                final_fees = c.fetchone()[0] or 0
                c.execute("SELECT COUNT(*) FROM enquiries WHERE status = 'New'")
                new_enquiries = c.fetchone()[0]
                conn.close()

                self.send_json({
                    "total_members": total_members,
                    "brides_count": brides_count,
                    "grooms_count": grooms_count,
                    "pending_approvals": pending_count,
                    "approved_profiles": approved_count,
                    "rejected_profiles": rejected_count,
                    "pending_payments_count": pending_payments,
                    "registration_revenue": reg_fees,
                    "finalisation_revenue": final_fees,
                    "total_revenue": reg_fees + final_fees,
                    "new_enquiries": new_enquiries
                })
                return

            # Registration Payments Queue (Mandatory ₹2,000 GPay Verification)
            elif clean_path == "/api/admin/registration-payments":
                qs = parse_qs(parsed.query)
                status_filter = qs.get("status", ["all"])[0]
                query = "SELECT * FROM registration_payments WHERE 1=1"
                params = []
                if status_filter != "all":
                    query += " AND status = ?"
                    params.append(status_filter)
                query += " ORDER BY id DESC"
                c.execute(query, params)
                records = [dict(r) for r in c.fetchall()]
                conn.close()
                self.send_json({"payments": records})
                return

            # Members list
            elif clean_path == "/api/admin/members":
                qs = parse_qs(parsed.query)
                status_filter = qs.get("status", ["all"])[0]
                search = qs.get("q", [""])[0]

                query = "SELECT * FROM profiles WHERE 1=1"
                params = []
                if status_filter != "all":
                    query += " AND status = ?"
                    params.append(status_filter)
                if search:
                    query += " AND (name LIKE ? OR id LIKE ? OR caste LIKE ? OR district LIKE ?)"
                    s = f"%{search}%"
                    params.extend([s, s, s, s])
                query += " ORDER BY reg_date DESC, id DESC"

                c.execute(query, params)
                members = [dict(row) for row in c.fetchall()]
                conn.close()
                self.send_json({"members": members})
                return

            # Payments list
            elif clean_path == "/api/admin/payments":
                c.execute("SELECT * FROM payments ORDER BY id DESC")
                payments = [dict(row) for row in c.fetchall()]
                conn.close()
                self.send_json({"payments": payments})
                return

            # Activity audit logs
            elif clean_path == "/api/admin/logs":
                c.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 100")
                logs = [dict(row) for row in c.fetchall()]
                conn.close()
                self.send_json({"logs": logs})
                return

            # Enquiries
            elif clean_path == "/api/admin/enquiries":
                c.execute("SELECT * FROM enquiries ORDER BY id DESC")
                enqs = [dict(row) for row in c.fetchall()]
                conn.close()
                self.send_json({"enquiries": enqs})
                return

            # Reports
            elif clean_path == "/api/admin/reports":
                c.execute("""
                SELECT pr.*, p.name as reported_name, p.district as reported_district
                FROM profile_reports pr
                JOIN profiles p ON pr.reported_profile_id = p.id
                ORDER BY pr.id DESC
                """)
                reports = [dict(row) for row in c.fetchall()]
                conn.close()
                self.send_json({"reports": reports})
                return

            conn.close()
            self.send_json({"error": "Unknown admin endpoint"}, status=404)
            return

        # Default static file serving (for public website)
        return super().do_GET()

    # --------------------------------------------------------------------------
    # POST Handling
    # --------------------------------------------------------------------------
    def do_POST(self):
        parsed = urlparse(self.path)
        clean_path = parsed.path.rstrip("/")
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""

        data = {}
        if post_data:
            try:
                data = json.loads(post_data.decode("utf-8"))
            except Exception:
                pass

        # 1. USER REGISTRATION (Step 1: Creates account + initiates GPay ₹2,000 Payment Workflow)
        if clean_path == "/api/auth/register":
            name = data.get("name", "").strip()
            email = data.get("email", "").strip().lower()
            phone = data.get("phone", "").strip()
            dob = data.get("dob", "").strip()
            gender = data.get("gender", "").strip().lower()
            password = data.get("password", "")
            caste = data.get("caste", "Mudaliar").strip()
            district = data.get("district", "Kanchipuram").strip()
            education = data.get("education", "").strip()
            occupation = data.get("occupation", "").strip()

            if not name or not email or not phone or not dob or not gender or not password:
                self.send_json({"error": "All required fields must be completed"}, status=400)
                return

            # Age validation (Minimum 18 years)
            try:
                birth = datetime.strptime(dob, "%Y-%m-%d")
                age = (datetime.now() - birth).days // 365
                if age < 18:
                    self.send_json({"error": "Candidate must be at least 18 years of age"}, status=400)
                    return
            except Exception:
                age = 25

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            # Duplicate email or mobile check
            c.execute("SELECT id FROM users WHERE email = ? OR phone = ?", (email, phone))
            if c.fetchone():
                conn.close()
                self.send_json({"error": "An account with this email or mobile number already exists"}, status=400)
                return

            # Create User Record (Status: PENDING payment)
            user_id = f"USR-{secrets.token_hex(4).upper()}"
            pw_hash, salt = hash_password(password)
            c.execute("""
            INSERT INTO users (id, email, phone, name, password_hash, salt, role, status)
            VALUES (?, ?, ?, ?, ?, ?, 'user', 'pending')
            """, (user_id, email, phone, name, pw_hash, salt))

            # Create Profile Record (Status: pending) with sequential unique SMK-2026-XXXXXX ID
            profile_id = generate_unique_profile_id(c, 2026)
            subcaste = data.get("sub_caste", "").strip()
            marriage_timeline = data.get("marriage_timeline", "Flexible").strip()
            photo_url = data.get("photo_url", "").strip()
            if not photo_url:
                photo_url = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80" if gender == "female" else "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80"

            c.execute("""
            INSERT INTO profiles (
                id, user_id, name, gender, age, religion, caste, subcaste, district,
                education, occupation, photo_url, is_approved, status, payment_status,
                reg_date, phone, email, completion_percentage
            ) VALUES (
                ?, ?, ?, ?, ?, 'Hindu', ?, ?, ?,
                ?, ?, ?, 0, 'pending', 'Pending (₹2,000)',
                ?, ?, ?, 75
            )
            """, (
                profile_id, user_id, name, gender, age, caste, subcaste, district,
                education, occupation, photo_url, datetime.now().strftime("%Y-%m-%d"), phone, email
            ))

            # Create Registration Payment Record (Mandatory GPay ₹2,000)
            reg_id = f"REG-2026-{secrets.token_hex(4).upper()}"
            c.execute("""
            INSERT INTO registration_payments (
                registration_id, user_id, profile_id, applicant_name, applicant_phone,
                applicant_email, amount, payee_number, payee_name, payment_method, status
            ) VALUES (?, ?, ?, ?, ?, ?, 2000, '9942006877', 'Sarvamangala Matrimony (GPay)', 'Google Pay / UPI', 'PENDING')
            """, (reg_id, user_id, profile_id, name, phone, email))

            conn.commit()
            conn.close()

            # Return Payment Instructions for ₹2,000 via GPay
            upi_intent = f"upi://pay?pa=9942006877@upi&pn=Sarvamangala%20Matrimony&am=2000&cu=INR&tn={reg_id}"
            self.send_json({
                "success": True,
                "message": "Registration submitted. Please complete ₹2,000 registration fee via Google Pay (GPay).",
                "registration_id": reg_id,
                "profile_id": profile_id,
                "user_id": user_id,
                "payment": {
                    "amount": 2000,
                    "payee_name": "Sarvamangala Matrimony",
                    "payee_number": "9942006877",
                    "method": "Google Pay (GPay) / UPI",
                    "upi_id": "9942006877@upi",
                    "upi_intent": upi_intent,
                    "status": "PENDING"
                }
            })
            return

        # 2. SUBMIT GPAY TRANSACTION REFERENCE (Step 2 of Registration)
        elif clean_path == "/api/auth/submit-payment":
            reg_id = data.get("registration_id", "").strip()
            txn_ref = data.get("txn_ref", "").strip()

            if not reg_id or not txn_ref:
                self.send_json({"error": "Registration ID and UPI Transaction Reference are required"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            # Prevent duplicate transaction reference usage
            c.execute("SELECT id FROM registration_payments WHERE txn_ref = ? AND registration_id != ?", (txn_ref, reg_id))
            if c.fetchone():
                conn.close()
                self.send_json({"error": "This UPI Transaction Reference has already been submitted"}, status=400)
                return

            c.execute("""
            UPDATE registration_payments
            SET txn_ref = ?, status = 'PAYMENT_SUBMITTED', submitted_at = CURRENT_TIMESTAMP
            WHERE registration_id = ?
            """, (txn_ref, reg_id))

            if c.rowcount == 0:
                conn.close()
                self.send_json({"error": "Registration record not found"}, status=404)
                return

            conn.commit()
            conn.close()

            self.send_json({
                "success": True,
                "status": "PAYMENT_SUBMITTED",
                "message": "Payment reference submitted successfully. Our Kanchipuram office will verify transaction records and activate your account shortly."
            })
            return

        # 3. USER LOGIN (with account verification & payment status checks)
        elif clean_path == "/api/auth/login":
            identifier = data.get("identifier", "").strip().lower()
            password = data.get("password", "")

            if not identifier or not password:
                self.send_json({"error": "Email/Phone and password are required"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Check if admin is logging in via standard form
            c.execute("SELECT id, name, email, password_hash, salt, role FROM admin_users WHERE LOWER(email) = ?", (identifier,))
            admin_row = c.fetchone()
            if admin_row and verify_password(password, admin_row["password_hash"], admin_row["salt"]):
                token = secrets.token_hex(32)
                expires = (datetime.now() + timedelta(hours=24)).isoformat()
                c.execute("INSERT INTO sessions (token, user_id, email, role, expires_at) VALUES (?, ?, ?, 'admin', ?)",
                          (token, f"ADM-{admin_row['id']}", admin_row["email"], expires))
                conn.commit()
                conn.close()
                cookie_val = f"sm_admin_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400"
                self.send_json({
                    "success": True,
                    "token": token,
                    "is_admin": True,
                    "user": {"name": admin_row["name"], "email": admin_row["email"], "role": "admin"}
                }, extra_headers={"Set-Cookie": cookie_val})
                return

            # Check regular members
            c.execute("SELECT * FROM users WHERE LOWER(email) = ? OR phone = ?", (identifier, identifier))
            user_row = c.fetchone()
            if not user_row or not verify_password(password, user_row["password_hash"], user_row["salt"]):
                conn.close()
                self.send_json({"error": "Invalid email/phone or password"}, status=401)
                return

            user = dict(user_row)

            # Check Payment & Account Status
            if user["status"] == "pending":
                c.execute("SELECT registration_id, status FROM registration_payments WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user["id"],))
                pay_row = c.fetchone()
                pay_status = pay_row["status"] if pay_row else "PENDING"
                reg_id = pay_row["registration_id"] if pay_row else ""
                conn.close()

                if pay_status == "PENDING":
                    self.send_json({
                        "error": "Registration fee of ₹2,000 is pending. Please complete payment via Google Pay to 9942006877.",
                        "payment_required": True,
                        "status": "PENDING",
                        "registration_id": reg_id
                    }, status=403)
                    return
                elif pay_status == "PAYMENT_SUBMITTED":
                    self.send_json({
                        "error": "Your ₹2,000 GPay payment has been submitted and is currently awaiting admin verification.",
                        "payment_pending_verification": True,
                        "status": "PAYMENT_SUBMITTED",
                        "registration_id": reg_id
                    }, status=403)
                    return

            if user["status"] == "suspended":
                conn.close()
                self.send_json({"error": "Your account has been suspended. Please contact Kanchipuram office at 8248853928."}, status=403)
                return

            # Active user: create session
            token = secrets.token_hex(32)
            expires = (datetime.now() + timedelta(days=7)).isoformat()
            c.execute("INSERT INTO sessions (token, user_id, email, role, expires_at) VALUES (?, ?, ?, 'user', ?)",
                      (token, user["id"], user["email"], expires))

            # Fetch linked profile
            c.execute("SELECT * FROM profiles WHERE user_id = ? OR email = ?", (user["id"], user["email"]))
            prof_row = c.fetchone()
            profile_data = dict(prof_row) if prof_row else None

            conn.commit()
            conn.close()

            self.send_json({
                "success": True,
                "token": token,
                "is_admin": False,
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "phone": user["phone"],
                    "role": user["role"],
                    "membership_plan": user["membership_plan"],
                    "membership_expiry": user.get("membership_expiry")
                },
                "profile": profile_data
            })
            return

        # 4. USER LOGOUT
        elif clean_path == "/api/auth/logout":
            token = self.extract_token()
            if token:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
                conn.close()
            self.send_json({"success": True, "message": "Logged out successfully"})
            return

        # 5. FORGOT PASSWORD
        elif clean_path == "/api/auth/forgot-password":
            email = data.get("email", "").strip().lower()
            if not email:
                self.send_json({"error": "Email is required"}, status=400)
                return
            # Safe response (does not leak email existence)
            self.send_json({
                "success": True,
                "message": "If an account exists with this email, password reset instructions have been sent. You can also contact our Kanchipuram office at 8248853928."
            })
            return

        # 6. MEMBER PROFILE EDIT
        elif clean_path == "/api/profile/edit":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            # Update core profile
            c.execute("""
            UPDATE profiles SET
                name = COALESCE(?, name),
                age = COALESCE(?, age),
                height = COALESCE(?, height),
                caste = COALESCE(?, caste),
                subcaste = COALESCE(?, subcaste),
                district = COALESCE(?, district),
                city = COALESCE(?, city),
                education = COALESCE(?, education),
                occupation = COALESCE(?, occupation),
                income = COALESCE(?, income),
                marital_status = COALESCE(?, marital_status),
                rasi = COALESCE(?, rasi),
                nakshatra = COALESCE(?, nakshatra),
                dosham = COALESCE(?, dosham),
                partner_pref = COALESCE(?, partner_pref),
                completion_percentage = 95
            WHERE id = ?
            """, (
                data.get("name"), data.get("age"), data.get("height"),
                data.get("caste"), data.get("subcaste"), data.get("district"),
                data.get("city"), data.get("education"), data.get("occupation"),
                data.get("income"), data.get("marital_status"), data.get("rasi"),
                data.get("nakshatra"), data.get("dosham"), data.get("partner_pref"),
                my_pid
            ))

            # Update family details
            c.execute("""
            INSERT INTO family_details (profile_id, father_name, father_occupation, mother_name, mother_occupation, brothers, sisters, native_place)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_id) DO UPDATE SET
                father_name = excluded.father_name,
                father_occupation = excluded.father_occupation,
                mother_name = excluded.mother_name,
                mother_occupation = excluded.mother_occupation,
                brothers = excluded.brothers,
                sisters = excluded.sisters,
                native_place = excluded.native_place
            """, (
                my_pid, data.get("father_name", ""), data.get("father_occupation", ""),
                data.get("mother_name", ""), data.get("mother_occupation", ""),
                int(data.get("brothers", 0) or 0), int(data.get("sisters", 0) or 0),
                data.get("native_place", "")
            ))

            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Profile updated successfully"})
            return

        # 7. MEMBER PHOTO UPLOAD
        elif clean_path == "/api/profile/upload-photo":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            img_b64 = data.get("image_base64", "")
            if not img_b64:
                self.send_json({"error": "Image data required"}, status=400)
                return

            try:
                # Strip header if present: data:image/png;base64,...
                if "," in img_b64:
                    img_b64 = img_b64.split(",", 1)[1]
                raw_bytes = base64.b64decode(img_b64)
                if len(raw_bytes) > 5 * 1024 * 1024:
                    self.send_json({"error": "Image size exceeds 5MB limit"}, status=400)
                    return

                filename = f"photo_{my_pid}_{secrets.token_hex(4)}.jpg"
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(raw_bytes)

                rel_url = f"assets/uploads/{filename}"
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("UPDATE profiles SET photo_url = ? WHERE id = ?", (rel_url, my_pid))
                conn.commit()
                conn.close()

                self.send_json({"success": True, "photo_url": rel_url})
                return
            except Exception as e:
                self.send_json({"error": f"Failed to save image: {e}"}, status=500)
                return

        # 8. SEND INTEREST
        elif clean_path == "/api/interests/send":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            receiver_id = data.get("receiver_id", "").strip()
            msg = data.get("message", "We reviewed your matrimonial biodata and are interested in connecting.")
            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])

            if not receiver_id or receiver_id == my_pid:
                self.send_json({"error": "Invalid profile selection"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            try:
                c.execute("""
                INSERT INTO interests (sender_id, receiver_id, status, message)
                VALUES (?, ?, 'pending', ?)
                ON CONFLICT(sender_id, receiver_id) DO UPDATE SET
                    status = 'pending', message = excluded.message, updated_at = CURRENT_TIMESTAMP
                """, (my_pid, receiver_id, msg))

                # Create notification for receiver
                c.execute("SELECT user_id, name FROM profiles WHERE id = ?", (receiver_id,))
                rec_row = c.fetchone()
                if rec_row and rec_row[0]:
                    c.execute("""
                    INSERT INTO notifications (user_id, title, message, type, link)
                    VALUES (?, 'New Interest Received', ?, 'interest', '#interests')
                    """, (rec_row[0], f"You received a new interest from {user['name']} ({my_pid})!"))

                conn.commit()
                conn.close()
                self.send_json({"success": True, "message": "Interest sent successfully"})
                return
            except Exception as e:
                conn.close()
                self.send_json({"error": f"Failed to send interest: {e}"}, status=500)
                return

        # 9. RESPOND TO INTEREST (Accept / Decline)
        elif clean_path == "/api/interests/respond":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            interest_id = data.get("interest_id")
            action = data.get("action", "").lower()
            if action not in ["accept", "decline"]:
                self.send_json({"error": "Action must be 'accept' or 'decline'"}, status=400)
                return

            new_status = "accepted" if action == "accept" else "declined"
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE interests SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, interest_id))
            
            # Notify sender
            c.execute("SELECT sender_id FROM interests WHERE id = ?", (interest_id,))
            s_row = c.fetchone()
            if s_row:
                c.execute("SELECT user_id FROM profiles WHERE id = ?", (s_row[0],))
                u_row = c.fetchone()
                if u_row and u_row[0]:
                    title = "Interest Accepted!" if action == "accept" else "Interest Update"
                    msg = f"{user['name']} has {new_status} your interest."
                    c.execute("INSERT INTO notifications (user_id, title, message, type, link) VALUES (?, ?, ?, 'interest', '#interests')",
                              (u_row[0], title, msg))

            conn.commit()
            conn.close()
            self.send_json({"success": True, "status": new_status})
            return

        # 10. WITHDRAW INTEREST
        elif clean_path == "/api/interests/withdraw":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return
            interest_id = data.get("interest_id")
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE interests SET status = 'withdrawn', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (interest_id,))
            conn.commit()
            conn.close()
            self.send_json({"success": True, "status": "withdrawn"})
            return

                # 8b. SECRET LIKES TOGGLE & MUTUAL MATCHING
        elif clean_path == "/api/secret-likes/toggle":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            target_pid = data.get("target_profile_id", "").strip()
            if not target_pid or target_pid == my_pid:
                self.send_json({"error": "Invalid profile selection"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Check tier limits
            allowed, limit_msg = check_tier_limit(c, user["user_id"], user.get("membership_plan"), "secret_likes")

            # Check if already liked
            c.execute("SELECT id, is_mutual FROM secret_likes WHERE sender_profile_id = ? AND target_profile_id = ?", (my_pid, target_pid))
            row = c.fetchone()
            if row:
                c.execute("DELETE FROM secret_likes WHERE sender_profile_id = ? AND target_profile_id = ?", (my_pid, target_pid))
                c.execute("UPDATE secret_likes SET is_mutual = 0 WHERE sender_profile_id = ? AND target_profile_id = ?", (target_pid, my_pid))
                conn.commit()
                conn.close()
                self.send_json({"success": True, "liked": False, "is_mutual": False, "message": "Secret like removed"})
                return

            if not allowed:
                conn.close()
                self.send_json({"error": limit_msg}, status=403)
                return

            # Check if target already liked sender -> Mutual match!
            c.execute("SELECT id FROM secret_likes WHERE sender_profile_id = ? AND target_profile_id = ?", (target_pid, my_pid))
            target_liked = c.fetchone()

            is_mutual = 1 if target_liked else 0
            c.execute("INSERT INTO secret_likes (sender_profile_id, target_profile_id, is_mutual) VALUES (?, ?, ?)", (my_pid, target_pid, is_mutual))

            if is_mutual:
                c.execute("UPDATE secret_likes SET is_mutual = 1 WHERE sender_profile_id = ? AND target_profile_id = ?", (target_pid, my_pid))
                # Send notifications to both
                c.execute("SELECT user_id, name FROM profiles WHERE id = ?", (target_pid,))
                target_user_row = c.fetchone()
                if target_user_row and target_user_row[0]:
                    c.execute("""
                    INSERT INTO notifications (user_id, title, message, type, link)
                    VALUES (?, '💖 Auspicious Mutual Match!', ?, 'match', '#mutual-matches')
                    """, (target_user_row[0], f"Congratulations! You and {user['name']} ({my_pid}) have both expressed mutual interest!"))
                
                c.execute("""
                INSERT INTO notifications (user_id, title, message, type, link)
                VALUES (?, '💖 Auspicious Mutual Match!', ?, 'match', '#mutual-matches')
                """, (user["user_id"], f"Congratulations! You and {target_user_row[1] if target_user_row else target_pid} have both expressed mutual interest!"))

            conn.commit()
            conn.close()
            msg = "🎉 Auspicious Mutual Match! Both of you have expressed interest." if is_mutual else "Secret Like recorded! It remains strictly private until they also express interest."
            self.send_json({"success": True, "liked": True, "is_mutual": bool(is_mutual), "message": msg})
            return

        # 9b. WISHLIST: REMOVE FROM SHORTLIST
        elif clean_path == "/api/shortlist/remove":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            pid = data.get("profile_id", "").strip()
            if not pid:
                self.send_json({"error": "Profile ID required"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("DELETE FROM shortlists WHERE user_id = ? AND profile_id = ?", (user["user_id"], pid))
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Profile removed from wishlist"})
            return

        # 9c. INTERESTS: WITHDRAW INTEREST REQUEST
        elif clean_path == "/api/interests/withdraw":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            receiver_id = data.get("receiver_id", "").strip()
            int_id = data.get("interest_id")

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            if int_id:
                c.execute("UPDATE interests SET status = 'withdrawn' WHERE id = ? AND sender_id = ?", (int_id, my_pid))
            elif receiver_id:
                c.execute("UPDATE interests SET status = 'withdrawn' WHERE sender_id = ? AND receiver_id = ?", (my_pid, receiver_id))
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Interest request withdrawn"})
            return

        # 9d. PRIVACY PLUS: SAVE SETTINGS
        elif clean_path == "/api/settings/privacy":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            photo_p = data.get("photo_privacy", "members_only")
            phone_p = data.get("phone_privacy", "consent_only")
            horoscope_p = data.get("horoscope_privacy", "members_only")

            if photo_p not in ["everyone", "members_only", "approved_contacts_only", "hidden"]:
                photo_p = "members_only"
            if phone_p not in ["members_only", "consent_only", "hidden"]:
                phone_p = "consent_only"
            if horoscope_p not in ["members_only", "consent_only"]:
                horoscope_p = "members_only"

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
            UPDATE profiles
            SET photo_privacy = ?, phone_privacy = ?, horoscope_privacy = ?
            WHERE id = ? OR user_id = ?
            """, (photo_p, phone_p, horoscope_p, my_pid, user["user_id"]))
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Privacy Plus preferences saved securely."})
            return

        # 9e. KANCHI SILK TRUST: APPLY / SUBMIT DOCUMENT REFERENCE
        elif clean_path == "/api/profile/apply-trust-badge":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            doc_ref = data.get("document_reference", "Aadhaar / Family Verification Reference").strip()

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
            UPDATE profiles
            SET trust_badge_status = 'pending', trust_badge_doc = ?
            WHERE id = ? OR user_id = ?
            """, (doc_ref, my_pid, user["user_id"]))
            conn.commit()
            conn.close()
            self.send_json({
                "success": True,
                "message": "Kanchi Silk Trust verification request submitted! Our Kanchipuram office will verify records."
            })
            return

        # 9f. ICE BREAKERS: SEND QUESTION
        elif clean_path == "/api/icebreakers/send":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            receiver_id = data.get("receiver_id", "").strip()
            question = data.get("question", "").strip()

            if not receiver_id or not question or receiver_id == my_pid:
                self.send_json({"error": "Valid recipient and question required"}, status=400)
                return

            if question not in PRESET_ICE_BREAKERS and len(question) > 300:
                self.send_json({"error": "Invalid ice breaker question format"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            allowed, limit_msg = check_tier_limit(c, user["user_id"], user.get("membership_plan"), "icebreaker")
            if not allowed:
                conn.close()
                self.send_json({"error": limit_msg}, status=403)
                return

            c.execute("SELECT id FROM ice_breakers WHERE sender_id = ? AND receiver_id = ? AND status = 'sent'", (my_pid, receiver_id))
            if c.fetchone():
                conn.close()
                self.send_json({"error": "An ice breaker question is already awaiting response from this member."}, status=400)
                return

            c.execute("""
            INSERT INTO ice_breakers (sender_id, receiver_id, question, status)
            VALUES (?, ?, ?, 'sent')
            """, (my_pid, receiver_id, question))

            c.execute("SELECT user_id FROM profiles WHERE id = ?", (receiver_id,))
            rec_row = c.fetchone()
            if rec_row and rec_row[0]:
                c.execute("""
                INSERT INTO notifications (user_id, title, message, type, link)
                VALUES (?, '🪔 Ice Breaker Received', ?, 'interest', '#icebreakers')
                """, (rec_row[0], f"{user['name']} ({my_pid}) sent you an Ice Breaker question: '{question}'"))

            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Ice Breaker sent successfully!"})
            return

        # 9g. ICE BREAKERS: REPLY
        elif clean_path == "/api/icebreakers/reply":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            ib_id = data.get("icebreaker_id")
            answer = data.get("answer", "").strip()

            if not ib_id or not answer:
                self.send_json({"error": "Question ID and answer are required"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT sender_id FROM ice_breakers WHERE id = ? AND receiver_id = ?", (ib_id, my_pid))
            row = c.fetchone()
            if not row:
                conn.close()
                self.send_json({"error": "Ice breaker question not found or unauthorized"}, status=404)
                return

            sender_pid = row[0]
            c.execute("""
            UPDATE ice_breakers
            SET answer = ?, status = 'answered', answered_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (answer, ib_id))

            c.execute("SELECT user_id FROM profiles WHERE id = ?", (sender_pid,))
            s_row = c.fetchone()
            if s_row and s_row[0]:
                c.execute("""
                INSERT INTO notifications (user_id, title, message, type, link)
                VALUES (?, '💬 Ice Breaker Answered', ?, 'interest', '#icebreakers')
                """, (s_row[0], f"{user['name']} has answered your Ice Breaker question!"))

            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Response submitted successfully!"})
            return

        # 11. SHORTLIST TOGGLE
        elif clean_path == "/api/shortlist/toggle":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            profile_id = data.get("profile_id", "").strip()
            if not profile_id:
                self.send_json({"error": "Profile ID required"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id FROM shortlists WHERE user_id = ? AND profile_id = ?", (user["user_id"], profile_id))
            row = c.fetchone()
            if row:
                c.execute("DELETE FROM shortlists WHERE id = ?", (row[0],))
                shortlisted = False
                msg = "Removed from favourites"
            else:
                c.execute("INSERT INTO shortlists (user_id, profile_id) VALUES (?, ?)", (user["user_id"], profile_id))
                shortlisted = True
                msg = "Added to favourites"

            conn.commit()
            conn.close()
            self.send_json({"success": True, "shortlisted": shortlisted, "message": msg})
            return

        # 12. CONTACT REQUEST (Request / Respond)
        elif clean_path == "/api/contact-requests/request":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            target_id = data.get("target_id", "").strip()
            my_pid = user.get("profile", {}).get("profile_id", user["user_id"])
            if not target_id or target_id == my_pid:
                self.send_json({"error": "Invalid profile selection"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
            INSERT INTO contact_requests (requester_id, target_id, status)
            VALUES (?, ?, 'pending')
            ON CONFLICT(requester_id, target_id) DO UPDATE SET status = 'pending', updated_at = CURRENT_TIMESTAMP
            """, (my_pid, target_id))

            # Notify target
            c.execute("SELECT user_id FROM profiles WHERE id = ?", (target_id,))
            t_row = c.fetchone()
            if t_row and t_row[0]:
                c.execute("""
                INSERT INTO notifications (user_id, title, message, type, link)
                VALUES (?, 'Contact Request Received', ?, 'contact', '#contact-requests')
                """, (t_row[0], f"{user['name']} has requested to view your family contact numbers."))

            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Contact request submitted to family"})
            return

        elif clean_path == "/api/contact-requests/respond":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            req_id = data.get("request_id")
            action = data.get("action", "").lower()
            new_status = "approved" if action == "approve" else "rejected"

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE contact_requests SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, req_id))
            
            # Notify requester
            c.execute("SELECT requester_id FROM contact_requests WHERE id = ?", (req_id,))
            r_row = c.fetchone()
            if r_row:
                c.execute("SELECT user_id FROM profiles WHERE id = ?", (r_row[0],))
                u_row = c.fetchone()
                if u_row and u_row[0]:
                    if action == "approve":
                        msg = f"Good news! {user['name']} approved your contact request. You can now view their direct contact numbers."
                    else:
                        msg = f"{user['name']} was unable to share contact details at this time."
                    c.execute("INSERT INTO notifications (user_id, title, message, type, link) VALUES (?, 'Contact Request Update', ?, 'contact', '#contact-requests')",
                              (u_row[0], msg))

            conn.commit()
            conn.close()
            self.send_json({"success": True, "status": new_status})
            return

        # 13. NOTIFICATIONS MARK AS READ
        elif clean_path == "/api/notifications/read":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            notif_id = data.get("notification_id")
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            if notif_id:
                c.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notif_id, user["user_id"]))
            else:
                c.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user["user_id"],))
            conn.commit()
            conn.close()
            self.send_json({"success": True})
            return

        # 14. SETTINGS: CHANGE PASSWORD
        elif clean_path == "/api/settings/change-password":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            old_pw = data.get("current_password", "")
            new_pw = data.get("new_password", "")
            if not old_pw or not new_pw or len(new_pw) < 6:
                self.send_json({"error": "Valid current password and new password (min 6 characters) are required"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT password_hash, salt FROM users WHERE id = ?", (user["user_id"],))
            row = c.fetchone()
            if not row or not verify_password(old_pw, row[0], row[1]):
                conn.close()
                self.send_json({"error": "Current password is incorrect"}, status=400)
                return

            new_hash, new_salt = hash_password(new_pw)
            c.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (new_hash, new_salt, user["user_id"]))
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Password changed successfully"})
            return

        # 15. SETTINGS: PROFILE VISIBILITY & DEACTIVATE
        elif clean_path == "/api/settings/visibility":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            is_hidden = 1 if data.get("is_hidden") else 0
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE profiles SET is_hidden = ? WHERE user_id = ?", (is_hidden, user["user_id"]))
            conn.commit()
            conn.close()
            msg = "Profile hidden from public match directory" if is_hidden else "Profile visible in match directory"
            self.send_json({"success": True, "is_hidden": is_hidden, "message": msg})
            return

        elif clean_path == "/api/settings/delete-request":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized()
                return

            reason = data.get("reason", "User requested account deactivation")
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE users SET status = 'deactivation_requested' WHERE id = ?", (user["user_id"],))
            c.execute("UPDATE profiles SET is_hidden = 1 WHERE user_id = ?", (user["user_id"],))
            conn.commit()
            conn.close()
            log_activity("SYSTEM", "Account Deactivation Requested", user["user_id"], reason)
            self.send_json({"success": True, "message": "Account deactivation request recorded. Our team will process this within 24 hours."})
            return

        # 15b. MEMBERSHIP PLAN SELECTION & SUBMISSION
        elif clean_path == "/api/membership/select":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized("Please log in to select a membership plan")
                return

            plan_id = data.get("plan_id", "").strip().lower()
            if not plan_id:
                self.send_json({"error": "Plan ID is required"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM membership_plans WHERE LOWER(id) = ?", (plan_id,))
            plan_row = c.fetchone()
            if not plan_row:
                conn.close()
                self.send_json({"error": "Invalid plan selected"}, status=404)
                return

            plan_dict = dict(plan_row)
            now = datetime.now()

            if plan_dict["price"] == 0:
                # Free Plan: activates immediately for logged-in user without payment
                start_date = now.strftime("%Y-%m-%d")
                expiry_date = (now + timedelta(days=plan_dict["validity_days"])).strftime("%Y-%m-%d")
                
                c.execute("""
                UPDATE users
                SET membership_plan = ?, membership_expiry = ?
                WHERE id = ?
                """, (plan_dict["name"], expiry_date, user["user_id"]))

                c.execute("""
                INSERT INTO user_memberships (user_id, plan_id, plan_name, price, validity_days, status, start_date, expiry_date, payment_method, txn_ref)
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?, 'Free (No Payment Required)', 'FREE-ACTIVATION')
                """, (user["user_id"], plan_dict["id"], plan_dict["name"], plan_dict["price"], plan_dict["validity_days"], start_date, expiry_date))

                c.execute("""
                INSERT INTO notifications (user_id, title, message, type, link)
                VALUES (?, 'Free Plan Activated!', 'Your Free Plan is active with profile creation, photo upload, and search privileges for 30 days.', 'system', '/membership-details')
                """, (user["user_id"],))

                log_activity(user["email"], "Free Plan Activated", user["user_id"], "Immediate activation of Free Plan")
                conn.commit()
                conn.close()

                self.send_json({
                    "success": True,
                    "status": "active",
                    "plan_id": plan_dict["id"],
                    "plan_name": plan_dict["name"],
                    "price": 0,
                    "validity_days": plan_dict["validity_days"],
                    "expiry_date": expiry_date,
                    "payment_required": False,
                    "message": f"{plan_dict['name']} activated immediately! Valid for {plan_dict['validity_days']} days."
                })
                return
            else:
                # Paid Plan (Gold or Diamond): payment confirmation required. Never fake payment success.
                c.execute("""
                INSERT INTO user_memberships (user_id, plan_id, plan_name, price, validity_days, status, payment_method, txn_ref)
                VALUES (?, ?, ?, ?, ?, 'pending_verification', 'Google Pay (9942006877)', NULL)
                """, (user["user_id"], plan_dict["id"], plan_dict["name"], plan_dict["price"], plan_dict["validity_days"]))
                membership_id = c.lastrowid

                reg_id = f"MEM-{datetime.now().strftime('%Y%m%d')}-{secrets.randbelow(8999)+1000}"
                c.execute("""
                INSERT INTO registration_payments (
                    registration_id, user_id, profile_id, applicant_name, applicant_phone, applicant_email,
                    amount, payee_number, payee_name, payment_method, status, plan_id, plan_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, '9942006877', 'Sarvamangala Matrimony (GPay)', 'Google Pay / UPI', 'PENDING', ?, ?)
                """, (
                    reg_id, user["user_id"], user.get("profile", {}).get("profile_id", user["user_id"]),
                    user["name"], user["phone"], user["email"],
                    plan_dict["price"], plan_dict["id"], plan_dict["name"]
                ))

                conn.commit()
                conn.close()

                self.send_json({
                    "success": True,
                    "status": "pending_verification",
                    "payment_required": True,
                    "membership_id": membership_id,
                    "registration_id": reg_id,
                    "plan_id": plan_dict["id"],
                    "plan_name": plan_dict["name"],
                    "price": plan_dict["price"],
                    "validity_days": plan_dict["validity_days"],
                    "payee_number": "9942006877",
                    "payee_name": "Sarvamangala Matrimony (GPay)",
                    "message": f"{plan_dict['name']} selected. Please complete payment of ₹{plan_dict['price']:,} via Google Pay (GPay) to 9942006877 and submit your UPI Reference ID."
                })
                return

        elif clean_path == "/api/membership/submit-payment":
            token = self.extract_token()
            user = verify_user_session(token)
            if not user:
                self.send_unauthorized("Please log in to submit payment reference")
                return

            plan_id = data.get("plan_id", "").strip().lower()
            txn_ref = data.get("txn_ref", "").strip()
            reg_id = data.get("registration_id", "").strip()

            if not txn_ref:
                self.send_json({"error": "UPI Transaction Reference (UTR / Txn ID) is required"}, status=400)
                return

            if len(txn_ref) < 6:
                self.send_json({"error": "Please enter a valid UPI Transaction Reference ID (at least 6 characters)"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Prevent duplicate transaction reference usage
            c.execute("SELECT id FROM registration_payments WHERE txn_ref = ? AND user_id != ?", (txn_ref, user["user_id"]))
            if c.fetchone():
                conn.close()
                self.send_json({"error": "This UPI Transaction Reference has already been submitted by another user"}, status=400)
                return

            # Update latest user_memberships entry
            c.execute("""
            UPDATE user_memberships
            SET txn_ref = ?, status = 'pending_verification'
            WHERE user_id = ? AND (plan_id = ? OR ? = '')
            """, (txn_ref, user["user_id"], plan_id, plan_id))

            # Update registration_payments record
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if reg_id:
                c.execute("""
                UPDATE registration_payments
                SET txn_ref = ?, status = 'PAYMENT_SUBMITTED', submitted_at = ?
                WHERE registration_id = ? AND user_id = ?
                """, (txn_ref, now_str, reg_id, user["user_id"]))
            else:
                c.execute("""
                UPDATE registration_payments
                SET txn_ref = ?, status = 'PAYMENT_SUBMITTED', submitted_at = ?
                WHERE user_id = ? AND status = 'PENDING'
                """, (txn_ref, now_str, user["user_id"]))

            # Notify user
            c.execute("""
            INSERT INTO notifications (user_id, title, message, type, link)
            VALUES (?, 'Payment Reference Submitted', ?, 'verification', '/membership-details')
            """, (user["user_id"], f"Payment reference {txn_ref} received. Admin verification is pending at our Kanchipuram office."))

            log_activity(user["email"], "Membership Payment Submitted", user["user_id"], f"Txn Ref: {txn_ref} for plan: {plan_id}")
            conn.commit()
            conn.close()

            self.send_json({
                "success": True,
                "status": "pending_verification",
                "txn_ref": txn_ref,
                "message": "Payment reference submitted successfully! Our Kanchipuram office will verify the transaction against bank statement and activate your membership."
            })
            return

        # 16. REPORT PROFILE
        elif clean_path == "/api/public/report-profile":
            token = self.extract_token()
            user = verify_user_session(token)
            rep_id = user["user_id"] if user else "GUEST"
            target_pid = data.get("profile_id", "").strip()
            reason = data.get("reason", "").strip()
            details = data.get("details", "").strip()

            if not target_pid or not reason:
                self.send_json({"error": "Profile ID and reason are required"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
            INSERT INTO profile_reports (reporter_id, reported_profile_id, reason, details)
            VALUES (?, ?, ?, ?)
            """, (rep_id, target_pid, reason, details))
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Thank you for alerting us. Our trust & safety team will review this profile."})
            return

        # 17. CONTACT FORM ENQUIRY
        elif clean_path == "/api/public/enquiry":
            name = data.get("name", "").strip()
            phone = data.get("phone", "").strip()
            email = data.get("email", "").strip()
            subject = data.get("subject", "General Enquiry").strip()
            msg = data.get("message", "").strip()

            if name and phone:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("""
                INSERT INTO enquiries (name, phone, email, subject, message, district, status, date)
                VALUES (?, ?, ?, ?, ?, 'Kanchipuram', 'New', ?)
                """, (name, phone, email, subject, msg, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                self.send_json({"success": True, "message": "Enquiry received. Our Kanchipuram office will call your family shortly."})
                return
            self.send_json({"error": "Name and phone are required"}, status=400)
            return

        # 18. ADMIN AUTH & ACTIONS
        if clean_path == "/api/admin/login":
            email = (data.get("email") or data.get("username") or "").strip()
            password = data.get("password", "").strip()
            if not email or not password:
                self.send_json({"success": False, "error": "Email and password are required"}, status=400)
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id, name, password_hash, salt, role FROM admin_users WHERE email = ?", (email,))
            row = c.fetchone()
            if not row or not verify_password(password, row[2], row[3]):
                conn.close()
                log_activity(email or "UNKNOWN", "Failed Login Attempt", "AUTH", "Invalid admin credentials entered", self.client_address[0])
                self.send_json({"success": False, "error": "Invalid admin email or password"}, status=401)
                return

            user_id, name, _, _, role = row
            token = secrets.token_hex(32)
            expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
            c.execute("INSERT INTO sessions (token, user_id, email, role, expires_at) VALUES (?, ?, ?, ?, ?)",
                      (token, str(user_id), email, role, expires_at))
            conn.commit()
            conn.close()

            log_activity(email, "Admin Login", f"USER-{user_id}", f"Admin {name} logged in successfully", self.client_address[0])
            cookie_val = f"sm_admin_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400"
            self.send_json({
                "success": True,
                "token": token,
                "user": {"email": email, "name": name, "role": role}
            }, extra_headers={"Set-Cookie": cookie_val})
            return

        elif clean_path == "/api/admin/logout":
            token = self.extract_token()
            user = verify_admin_session(token)
            if user:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
                conn.close()
            cookie_val = "sm_admin_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
            self.send_json({"success": True, "message": "Admin logged out"}, extra_headers={"Set-Cookie": cookie_val})
            return

        # Protected Admin Actions
        if clean_path.startswith("/api/admin/"):
            token = self.extract_token()
            user = verify_admin_session(token)
            if not user:
                self.send_forbidden("Admin authorization required")
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # VERIFY GPAY ₹2,000 REGISTRATION PAYMENT (Approve & Activate Account!)
            if clean_path == "/api/admin/verify-payment":
                reg_id = data.get("registration_id")
                action = data.get("action", "approve")  # 'approve' or 'reject'
                notes = data.get("notes", "")

                if not reg_id:
                    conn.close()
                    self.send_json({"error": "Registration ID required"}, status=400)
                    return

                c.execute("SELECT * FROM registration_payments WHERE registration_id = ?", (reg_id,))
                payment_row = c.fetchone()
                if not payment_row:
                    conn.close()
                    self.send_json({"error": "Registration payment record not found"}, status=404)
                    return

                # row columns: id, registration_id, user_id, profile_id, applicant_name, applicant_phone, applicant_email, amount, payee_number, payee_name, payment_method, txn_ref, status, submitted_at, verified_at, verified_by, notes, receipt_number
                p_uid = payment_row[2]
                p_pid = payment_row[3]
                p_name = payment_row[4]
                p_amt = payment_row[7]
                p_txn = payment_row[11] or f"GPAY-{secrets.token_hex(4).upper()}"

                if action == "approve":
                    receipt_no = f"RCP-2026-{secrets.randbelow(89999) + 10000}"
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # 1. Update registration payment record
                    c.execute("""
                    UPDATE registration_payments
                    SET status = 'PAID', verified_at = ?, verified_by = ?, notes = ?, receipt_number = ?
                    WHERE registration_id = ?
                    """, (now_str, user["email"], notes or "Verified against GPay 9942006877 records", receipt_no, reg_id))

                    # 2. Activate User Account with Plan & Expiry
                    plan_to_activate = payment_row["plan_name"] if ("plan_name" in payment_row.keys() and payment_row["plan_name"]) else "Gold Plan"
                    days_valid = 365 if "diamond" in str(plan_to_activate).lower() else 180
                    exp_date = (datetime.now() + timedelta(days=days_valid)).strftime("%Y-%m-%d")

                    c.execute("UPDATE users SET status = 'active', membership_plan = ?, membership_expiry = ? WHERE id = ?", (plan_to_activate, exp_date, p_uid))

                    c.execute("""
                    UPDATE user_memberships
                    SET status = 'active', start_date = ?, expiry_date = ?
                    WHERE user_id = ? AND status = 'pending_verification'
                    """, (datetime.now().strftime("%Y-%m-%d"), exp_date, p_uid))

                    # 3. Approve Profile & Mark Payment as Paid
                    c.execute("""
                    UPDATE profiles
                    SET is_approved = 1, status = 'approved', payment_status = 'Paid (₹2,000)'
                    WHERE id = ? OR user_id = ?
                    """, (p_pid, p_uid))

                    # 4. Insert into General Payments ledger (so statistics and audit update)
                    c.execute("""
                    INSERT INTO payments (profile_id, profile_name, payment_type, amount, status, txn_id, method, date)
                    VALUES (?, ?, 'Registration Fee (₹2,000)', ?, 'Completed', ?, 'Google Pay (9942006877)', ?)
                    """, (p_pid, p_name, p_amt, p_txn, datetime.now().strftime("%Y-%m-%d")))

                    # 5. Create Notification for user
                    c.execute("""
                    INSERT INTO notifications (user_id, title, message, type, link)
                    VALUES (?, 'Registration Payment Verified!', 'Your ₹2,000 payment has been verified and your profile is now live.', 'verification', '#dashboard')
                    """, (p_uid,))

                    log_activity(user["email"], "Payment Verified & Account Activated", reg_id,
                                 f"Verified ₹{p_amt} GPay payment for {p_name} ({p_pid}). Receipt: {receipt_no}", self.client_address[0])

                    conn.commit()
                    conn.close()
                    self.send_json({
                        "success": True,
                        "action": "approved",
                        "registration_id": reg_id,
                        "receipt_number": receipt_no,
                        "message": f"Payment verified! Profile {p_pid} and User {p_uid} are now ACTIVE."
                    })
                    return

                elif action == "reject":
                    c.execute("""
                    UPDATE registration_payments
                    SET status = 'FAILED', verified_at = CURRENT_TIMESTAMP, verified_by = ?, notes = ?
                    WHERE registration_id = ?
                    """, (user["email"], notes or "Transaction reference could not be verified in GPay statement", reg_id))

                    log_activity(user["email"], "Payment Rejected", reg_id, f"Rejected payment claim for {p_name}. Reason: {notes}", self.client_address[0])
                    conn.commit()
                    conn.close()
                    self.send_json({"success": True, "action": "rejected", "registration_id": reg_id})
                    return

                        # Kanchi Silk Trust Badge Verification: approve or reject
            elif clean_path == "/api/admin/verify-trust-badge":
                pid = data.get("profile_id")
                action = data.get("action", "approve")  # 'approve' or 'reject'
                notes = data.get("notes", "")

                if not pid:
                    conn.close()
                    self.send_json({"error": "Profile ID required"}, status=400)
                    return

                new_status = "verified" if action == "approve" else "rejected"
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                c.execute("""
                UPDATE profiles
                SET trust_badge_status = ?, trust_badge_verified_at = ?, trust_badge_verified_by = ?
                WHERE id = ?
                """, (new_status, now_str, user["email"], pid))

                c.execute("SELECT user_id, name FROM profiles WHERE id = ?", (pid,))
                u_row = c.fetchone()
                if u_row and u_row[0]:
                    title = "🪔 Kanchi Silk Trust Badge Approved!" if action == "approve" else "Trust Badge Application Update"
                    msg = (f"Congratulations {u_row[1]}! Your profile has been awarded the official Kanchi Silk Trust Verified Badge."
                           if action == "approve" else
                           f"Your Kanchi Silk Trust application was reviewed. Note: {notes or 'Please re-verify documents with office.'}")
                    c.execute("""
                    INSERT INTO notifications (user_id, title, message, type, link)
                    VALUES (?, ?, ?, 'verification', '#dashboard')
                    """, (u_row[0], title, msg))

                log_activity(user["email"], f"Trust Badge {action.capitalize()}", pid, f"Admin {action}ed trust badge for {pid}. Notes: {notes}", self.client_address[0])
                conn.commit()
                conn.close()
                self.send_json({"success": True, "status": new_status, "profile_id": pid})
                return

            # Member Action: approve, reject, suspend, reactivate, delete
            elif clean_path == "/api/admin/member-action":
                pid = data.get("id")
                action = data.get("action")
                notes = data.get("notes", "")

                if action == "approve":
                    c.execute("UPDATE profiles SET status = 'approved', is_approved = 1, notes = ? WHERE id = ?", (notes, pid))
                    log_activity(user["email"], "Profile Approved", pid, f"Approved profile {pid}", self.client_address[0])
                elif action == "reject":
                    c.execute("UPDATE profiles SET status = 'rejected', is_approved = 0, notes = ? WHERE id = ?", (notes, pid))
                    log_activity(user["email"], "Profile Rejected", pid, f"Rejected profile {pid}. Reason: {notes}", self.client_address[0])
                elif action == "suspend":
                    c.execute("UPDATE profiles SET status = 'suspended', is_approved = 0, notes = ? WHERE id = ?", (notes, pid))
                    log_activity(user["email"], "Profile Suspended", pid, f"Suspended profile {pid}", self.client_address[0])
                elif action == "delete":
                    c.execute("DELETE FROM profiles WHERE id = ?", (pid,))
                    log_activity(user["email"], "Profile Deleted", pid, f"Deleted profile {pid}", self.client_address[0])

                conn.commit()
                conn.close()
                self.send_json({"success": True, "action": action, "id": pid})
                return

            # Record Manual / Finalisation Payment
            elif clean_path == "/api/admin/record-payment":
                pid = data.get("profile_id", "SM-MANUAL")
                pname = data.get("profile_name", "Member Alliance")
                ptype = data.get("payment_type", "Match Finalisation (₹25,000)")
                amount = int(data.get("amount", 25000))
                method = data.get("method", "Direct Bank Transfer")
                txn = f"TXN-{secrets.token_hex(4).upper()}"
                date_str = datetime.now().strftime("%Y-%m-%d")

                c.execute("""
                INSERT INTO payments (profile_id, profile_name, payment_type, amount, status, txn_id, method, date)
                VALUES (?, ?, ?, ?, 'Completed', ?, ?, ?)
                """, (pid, pname, ptype, amount, txn, method, date_str))
                conn.commit()
                conn.close()
                log_activity(user["email"], "Payment Recorded", txn, f"Recorded {ptype} of ₹{amount} for {pname}", self.client_address[0])
                self.send_json({"success": True, "txn_id": txn})
                return

            conn.close()
            self.send_json({"error": "Unknown admin POST endpoint"}, status=404)
            return

        self.send_json({"error": "Not Found"}, status=404)

# ==============================================================================
# Run Server
# ==============================================================================
if __name__ == "__main__":
    init_db()
    print("Sarvamangala Matrimony SQLite Database initialized successfully.", flush=True)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), MatrimonyServerHandler) as httpd:
        print("===============================================================", flush=True)
        print(f" Sarvamangala Matrimony Server running at http://0.0.0.0:{PORT}", flush=True)
        print(f" Public Website: http://0.0.0.0:{PORT}/", flush=True)
        print(f" Private Admin Portal: http://0.0.0.0:{PORT}/sm-admin", flush=True)
        print("===============================================================", flush=True)
        httpd.serve_forever()
