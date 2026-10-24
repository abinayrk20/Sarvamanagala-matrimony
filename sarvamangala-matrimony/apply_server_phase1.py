import re

server_path = "server.py"
with open(server_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update init_db with new columns and tables
cols_marker = '("is_hidden", "INTEGER DEFAULT 0")\n    ]'
new_cols_code = '''("is_hidden", "INTEGER DEFAULT 0"),
        ("marriage_timeline", "TEXT DEFAULT 'Flexible'"),
        ("trust_badge_status", "TEXT DEFAULT 'pending'"),
        ("trust_badge_doc", "TEXT DEFAULT 'Aadhaar / Family Verification Reference'"),
        ("trust_badge_verified_at", "TEXT"),
        ("trust_badge_verified_by", "TEXT"),
        ("photo_privacy", "TEXT DEFAULT 'members_only'"),
        ("phone_privacy", "TEXT DEFAULT 'consent_only'"),
        ("horoscope_privacy", "TEXT DEFAULT 'members_only'")
    ]'''

if cols_marker in content:
    content = content.replace(cols_marker, new_cols_code, 1)
    print("[OK] Added new columns to init_db()")

tables_marker = 'CREATE TABLE IF NOT EXISTS activity_logs ('
phase1_tables_code = '''CREATE TABLE IF NOT EXISTS secret_likes (
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

    CREATE TABLE IF NOT EXISTS activity_logs ('''

if tables_marker in content and 'CREATE TABLE IF NOT EXISTS secret_likes' not in content:
    content = content.replace(tables_marker, phase1_tables_code, 1)
    print("[OK] Added phase 1 & 2 tables to init_db()")

# 2. Add helper functions before MatrimonyServerHandler
helpers_marker = '# ==============================================================================\n# Custom Request Handler\n# =============================================================================='
phase1_helpers = '''# ==============================================================================
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
    "free": {"shortlist": 5, "interests": 2, "icebreaker": 1, "secret_likes": 1},
    "gold": {"shortlist": 35, "interests": 35, "icebreaker": 10, "secret_likes": 35},
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

    if is_self or is_admin:
        res["can_see_contact"] = True
        res["photo_masked"] = False
        return res

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

''' + helpers_marker

if 'generate_unique_profile_id' not in content:
    content = content.replace(helpers_marker, phase1_helpers, 1)
    print("[OK] Added Phase 1 helper functions")

with open(server_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Server helpers & schema updated!")
