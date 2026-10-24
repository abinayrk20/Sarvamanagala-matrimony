import sqlite3
import re
import os

DB_FILE = "sarvamangala_admin.db"

def migrate():
    print(f"Connecting to database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Add missing columns to profiles table
    c.execute("PRAGMA table_info(profiles)")
    cols = [col["name"] for col in c.fetchall()]

    new_cols = [
        ("marriage_timeline", "TEXT DEFAULT 'Flexible'"),
        ("trust_badge_status", "TEXT DEFAULT 'pending'"), # 'pending', 'verified', 'rejected'
        ("trust_badge_doc", "TEXT DEFAULT 'Aadhaar / Family Verification Reference'"),
        ("trust_badge_verified_at", "TEXT"),
        ("trust_badge_verified_by", "TEXT"),
        ("photo_privacy", "TEXT DEFAULT 'members_only'"), # 'everyone', 'members_only', 'approved_contacts_only', 'hidden'
        ("phone_privacy", "TEXT DEFAULT 'consent_only'"), # 'members_only', 'consent_only', 'hidden'
        ("horoscope_privacy", "TEXT DEFAULT 'members_only'"), # 'members_only', 'consent_only'
    ]

    for col_name, col_type in new_cols:
        if col_name not in cols:
            print(f"Adding column '{col_name}' to profiles...")
            c.execute(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}")

    # 2. Migrate Profile IDs to SMK-2026-000001 format
    c.execute("SELECT id FROM profiles ORDER BY rowid ASC")
    existing_profiles = [r[0] for r in c.fetchall()]
    print(f"Found {len(existing_profiles)} existing profiles to check/migrate.")

    id_map = {}
    seq = 1
    for old_id in existing_profiles:
        # Check if already follows SMK-2026-XXXXXX format
        if re.match(r"^SMK-2026-\d{6}$", old_id):
            new_id = old_id
            try:
                curr_seq = int(old_id.split("-")[-1])
                seq = max(seq, curr_seq + 1)
            except Exception:
                pass
        else:
            new_id = f"SMK-2026-{seq:06d}"
            seq += 1
            id_map[old_id] = new_id

    if id_map:
        print(f"Migrating {len(id_map)} profile IDs to SMK-2026-XXXXXX format...")
        for old_id, new_id in id_map.items():
            print(f"  {old_id} -> {new_id}")
            # Update profiles
            c.execute("UPDATE profiles SET id = ? WHERE id = ?", (new_id, old_id))
            # Update registration_payments
            c.execute("UPDATE registration_payments SET profile_id = ? WHERE profile_id = ?", (new_id, old_id))
            # Update family_details
            c.execute("UPDATE family_details SET profile_id = ? WHERE profile_id = ?", (new_id, old_id))
            # Update partner_preferences
            c.execute("UPDATE partner_preferences SET profile_id = ? WHERE profile_id = ?", (new_id, old_id))
            # Update shortlists
            c.execute("UPDATE shortlists SET profile_id = ? WHERE profile_id = ?", (new_id, old_id))
            # Update interests
            c.execute("UPDATE interests SET sender_id = ? WHERE sender_id = ?", (new_id, old_id))
            c.execute("UPDATE interests SET receiver_id = ? WHERE receiver_id = ?", (new_id, old_id))
            # Update contact_requests
            c.execute("UPDATE contact_requests SET requester_id = ? WHERE requester_id = ?", (new_id, old_id))
            c.execute("UPDATE contact_requests SET target_id = ? WHERE target_id = ?", (new_id, old_id))
            # Update payments
            c.execute("UPDATE payments SET profile_id = ? WHERE profile_id = ?", (new_id, old_id))

    # Set sample badges for demonstration:
    # Mark first 4 profiles as Verified so search and cards show the authentic Kanchi Silk Trust badge
    c.execute("SELECT id FROM profiles ORDER BY rowid ASC LIMIT 4")
    sample_pids = [r[0] for r in c.fetchall()]
    for pid in sample_pids:
        c.execute("""
        UPDATE profiles
        SET trust_badge_status = 'verified',
            trust_badge_verified_at = '2026-10-23 10:00:00',
            trust_badge_verified_by = 'admin@sarvamangala.com'
        WHERE id = ?
        """, (pid,))

    # 3. Create Secret Likes Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS secret_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_profile_id TEXT NOT NULL,
        target_profile_id TEXT NOT NULL,
        is_mutual INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(sender_profile_id, target_profile_id)
    )
    """)
    print("Created table: secret_likes")

    # 4. Create Ice Breakers Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS ice_breakers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id TEXT NOT NULL,
        receiver_id TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT,
        status TEXT DEFAULT 'sent', -- 'sent', 'answered', 'declined'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        answered_at TIMESTAMP
    )
    """)
    print("Created table: ice_breakers")

    # 5. PHASE 2 Architectural Schemas:
    # 5a. Horoscope Poruthams (10 Porutham Calculation Matrix)
    c.execute("""
    CREATE TABLE IF NOT EXISTS horoscope_poruthams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        boy_rasi TEXT NOT NULL,
        boy_nakshatra TEXT NOT NULL,
        girl_rasi TEXT NOT NULL,
        girl_nakshatra TEXT NOT NULL,
        dina_porutham INTEGER DEFAULT 1,
        gana_porutham INTEGER DEFAULT 1,
        mahendra_porutham INTEGER DEFAULT 1,
        sthree_dheerkha_porutham INTEGER DEFAULT 1,
        yoni_porutham INTEGER DEFAULT 1,
        rasi_porutham INTEGER DEFAULT 1,
        rasiyathipathi_porutham INTEGER DEFAULT 1,
        vasiya_porutham INTEGER DEFAULT 1,
        rajju_porutham INTEGER DEFAULT 1,
        vedha_porutham INTEGER DEFAULT 1,
        total_score INTEGER DEFAULT 8,
        compatibility_status TEXT DEFAULT 'Uthama Porutham (Excellent)',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Created table: horoscope_poruthams (Phase 2 Architectural schema)")

    # 5b. Local Connect (Radius & Location Discovery)
    c.execute("""
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
    )
    """)
    print("Created table: local_connect (Phase 2 Architectural schema)")

    # 5c. 30-Second Quick Intro (Video Profiles)
    c.execute("""
    CREATE TABLE IF NOT EXISTS quick_intros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id TEXT UNIQUE NOT NULL,
        video_url TEXT NOT NULL,
        duration_seconds INTEGER DEFAULT 30,
        thumbnail_url TEXT,
        status TEXT DEFAULT 'pending_review', -- 'pending_review', 'approved', 'rejected'
        visibility TEXT DEFAULT 'members_only',
        reviewed_by TEXT,
        reviewed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Created table: quick_intros (Phase 2 Architectural schema)")

    # 5d. Safe Audio/Video Calls (Consent & Logs)
    c.execute("""
    CREATE TABLE IF NOT EXISTS call_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caller_id TEXT NOT NULL,
        receiver_id TEXT NOT NULL,
        call_type TEXT DEFAULT 'audio', -- 'audio', 'video'
        channel_name TEXT NOT NULL,
        status TEXT DEFAULT 'requested', -- 'requested', 'accepted', 'completed', 'declined', 'cancelled'
        duration_seconds INTEGER DEFAULT 0,
        consent_caller INTEGER DEFAULT 1,
        consent_receiver INTEGER DEFAULT 0,
        started_at TIMESTAMP,
        ended_at TIMESTAMP,
        is_reported INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Created table: call_sessions (Phase 2 Architectural schema)")

    # Ensure a few marriage timelines exist on sample profiles
    timelines = ['Within 3 months', 'Within 6 months', 'Within 1 year', 'Flexible']
    c.execute("SELECT id FROM profiles")
    all_pids = [r[0] for r in c.fetchall()]
    for i, pid in enumerate(all_pids):
        tl = timelines[i % len(timelines)]
        c.execute("UPDATE profiles SET marriage_timeline = ? WHERE id = ? AND (marriage_timeline IS NULL OR marriage_timeline = 'Flexible')", (tl, pid))

    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
