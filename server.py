import http.server
import socketserver
import os
import sys
import json
import sqlite3
import hashlib
import secrets
import mimetypes
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

# ==============================================================================
# Database Initialization & Seed Data
# ==============================================================================
def hash_password(password: str, salt: str = None) -> tuple:
    if not salt:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return pw_hash, salt

def verify_password(password: str, pw_hash: str, salt: str) -> bool:
    check_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(check_hash, pw_hash)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Admin Users table
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

    # Sessions table
    c.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Profiles table
    c.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id TEXT PRIMARY KEY,
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
        notes TEXT
    )
    """)

    # Payments table
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

    # Admin Activity Logs table
    c.execute("""
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

    # Family Enquiries table
    c.execute("""
    CREATE TABLE IF NOT EXISTS enquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        message TEXT,
        district TEXT DEFAULT 'Kanchipuram',
        status TEXT DEFAULT 'New',
        date TEXT NOT NULL
    )
    """)

    # Seed Admin User if not exists
    c.execute("SELECT id FROM admin_users WHERE email = ?", ("admin@sarvamangala.com",))
    if not c.fetchone():
        pw_hash, salt = hash_password("KanchiMangala@2026")
        c.execute("""
        INSERT INTO admin_users (email, name, password_hash, salt, role)
        VALUES (?, ?, ?, ?, ?)
        """, ("admin@sarvamangala.com", "Temple City Administrator", pw_hash, salt, "admin"))

    # Seed initial profiles if empty
    c.execute("SELECT COUNT(*) FROM profiles")
    if c.fetchone()[0] == 0:
        seed_profiles = [
            ("SM-2026-9214", "Priya S.", "female", 25, "5 ft 4 in", "Hindu", "Mudaliar", "Thuluva Vellalar (Siva Gothram)", "Tamil", "Kanchipuram", "Kanchipuram", "Gandhi Road, Kanchipuram", "B.Tech (Information Technology)", "Software Engineer, Infosys (Hybrid)", "₹9.5 Lakhs / year", "Never Married", "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?auto=format&fit=crop&w=600&q=80", "Rishabam (Taurus)", "Rohini", "Simmam", "2001-05-14", "07:35 AM", "Kanchipuram", "None (தோஷமில்லை)", "jathagam_SM9214.pdf", "Groom: 26-29 yrs, B.E / B.Tech / MBA, Settled in Chennai or Kanchipuram, Mudaliar / Pillai, Non-Smoker.", 1, "approved", "Paid (₹2,000)", "2026-09-12", 92, "Verified with family visit"),
            ("SM-2026-8842", "Anitha R.", "female", 26, "5 ft 3 in", "Hindu", "Pillai", "Saiva Pillai", "Tamil", "Chengalpattu", "Chengalpattu", "Alagesan Nagar, Chengalpattu", "M.Sc Mathematics, B.Ed", "Senior Higher Secondary Lecturer", "₹6.2 Lakhs / year", "Never Married", "https://images.unsplash.com/photo-1594744803329-e58b31de8bf5?auto=format&fit=crop&w=600&q=80", "Kanni (Virgo)", "Hastham", "Kanni", "2000-08-22", "11:20 AM", "Chengalpattu", "None", "jathagam_SM8842.pdf", "Groom: 27-31 yrs, Master's degree / Govt employee or IT, Pillai / Mudaliar, values traditional family life.", 1, "approved", "Paid (₹2,000)", "2026-09-15", 86, "Horoscope 10 Porutham verified"),
            ("SM-2026-7310", "Vignesh M.", "male", 28, "5 ft 9 in", "Hindu", "Mudaliar", "Agamudayar", "Tamil", "Kanchipuram", "Kanchipuram", "Ekambareswarar Sannathi St, Kanchipuram", "B.E (Mechanical), MBA", "Senior Supply Chain Manager, Hyundai", "₹14.0 Lakhs / year", "Never Married", "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=600&q=80", "Mesham (Aries)", "Ashwini", "Mesham", "1998-04-10", "06:15 AM", "Kanchipuram", "None", "jathagam_SM7310.pdf", "Bride: 23-27 yrs, Graduate or Post Graduate, Tamil Hindu family values, non-demanding.", 1, "approved", "Paid (₹2,000)", "2026-09-18", 94, "Both families met at Kanchipuram office"),
            ("SM-2026-6190", "Karthik S.", "male", 29, "5 ft 10 in", "Hindu", "Vanniyar", "Padayatchi", "Tamil", "Vellore", "Vellore", "Katpadi Main Road, Vellore", "B.Tech, MS (Data Science)", "Lead Data Analyst, Cognizant Chennai", "₹18.5 Lakhs / year", "Never Married", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80", "Simmam (Leo)", "Makam", "Dhanusu", "1997-11-05", "03:45 PM", "Vellore", "None", "jathagam_SM6190.pdf", "Bride: 24-28 yrs, Any engineering or medical professional, willing to settle in Chennai or Vellore.", 1, "approved", "Paid (₹2,000)", "2026-09-20", 88, "ID verified"),
            ("SM-2026-5421", "Meenakshi V.", "female", 24, "5 ft 5 in", "Hindu", "Iyer", "Vadama (Kausika Gothram)", "Tamil", "Chennai", "Mylapore, Chennai", "North Mada Street, Mylapore", "B.Com, Chartered Accountant (CA Inter)", "Financial Audit Senior, EY Chennai", "₹11.0 Lakhs / year", "Never Married", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80", "Thulam (Libra)", "Swathi", "Thulam", "2002-01-19", "08:10 AM", "Chennai", "None", "jathagam_SM5421.pdf", "Groom: 26-30 yrs, CA / MBA / Tech professional, Vadama or Brahacharanam, vegetarian, Chennai settled.", 1, "approved", "Paid (₹2,000)", "2026-09-22", 91, "Traditional Vadama alliance"),
            ("SM-2026-4832", "Saravanan K.", "male", 31, "5 ft 8 in", "Hindu", "Chettiar", "Vaniya Chettiar", "Tamil", "Salem", "Salem", "Fairlands, Salem", "M.Tech (Civil Engineering)", "Class-I PWD Licensed Contractor & Builder", "₹22.0 Lakhs / year", "Never Married", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80", "Viruchigam (Scorpio)", "Anusham", "Kumbam", "1995-09-14", "10:05 AM", "Salem", "Chevvai (Mars - Parikaram done)", "jathagam_SM4832.pdf", "Bride: 25-29 yrs, Traditional family, Chettiar community, respects elders.", 1, "approved", "Paid (₹2,000)", "2026-09-25", 85, "Horoscope compatibility checked"),
            ("SM-2026-3105", "Deepa N.", "female", 27, "5 ft 2 in", "Hindu", "Naidu", "Kamma Naidu", "Tamil", "Tiruvallur", "Tiruvallur", "Jawahar Street, Tiruvallur", "B.Arch (Architecture)", "Chief Interior Architect, Private Studio", "₹8.0 Lakhs / year", "Never Married", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=600&q=80", "Kumbam (Aquarius)", "Sathayam", "Meenam", "1999-06-30", "01:25 PM", "Tiruvallur", "None", "jathagam_SM3105.pdf", "Groom: 28-32 yrs, Professional degree holder, Kamma / Balija Naidu, modern yet traditional outlook.", 1, "approved", "Paid (₹2,000)", "2026-09-28", 89, "Architecture portfolio verified"),
            ("SM-2026-2240", "Aravindhan B.", "male", 30, "5 ft 11 in", "Hindu", "Pillai", "Karkathar Pillai", "Tamil", "Madurai", "Madurai", "KK Nagar, Madurai", "MBBS, MD (General Medicine)", "Consultant Physician, Private Hospital", "₹24.0 Lakhs / year", "Never Married", "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?auto=format&fit=crop&w=600&q=80", "Dhanusu (Sagittarius)", "Moolam", "Simmam", "1996-03-08", "05:50 AM", "Madurai", "None", "jathagam_SM2240.pdf", "Bride: 25-29 yrs, Doctor (MBBS / BDS / MD) or Professional, Pillai / Saiva Pillai community, Madurai or South TN.", 1, "approved", "Paid (₹2,000)", "2026-10-01", 93, "Doctor alliance verified"),
            ("SM-2026-1055", "Kavitha M.", "female", 26, "5 ft 4 in", "Hindu", "Mudaliar", "Thuluva Vellalar", "Tamil", "Kanchipuram", "Kanchipuram", "Nellukara St, Kanchipuram", "B.E (ECE)", "Quality Analyst, TCS Siruseri", "₹7.5 Lakhs / year", "Never Married", "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=600&q=80", "Kanni (Virgo)", "Chithirai", "Thulam", "2000-10-10", "09:15 AM", "Kanchipuram", "None", "jathagam_SM1055.pdf", "Groom: 27-30 yrs, IT or Core engineer, Kanchipuram or Chennai.", 0, "pending", "Paid (₹2,000)", "2026-10-05", 87, "New registration - Pending document review")
        ]
        c.executemany("""
        INSERT INTO profiles (
            id, name, gender, age, height, religion, caste, subcaste, mother_tongue,
            district, city, address, education, occupation, income, marital_status,
            photo_url, rasi, nakshatra, lagnam, birth_date, birth_time, birth_place,
            dosham, jathagam_doc, partner_pref, is_approved, status, payment_status,
            reg_date, compatibility, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_profiles)

        # Seed payments
        seed_payments = [
            ("SM-2026-9214", "Priya S.", "Registration Fee (₹2,000)", 2000, "Completed", "TXN-UPI-98421092", "UPI (GPay)", "2026-09-12"),
            ("SM-2026-8842", "Anitha R.", "Registration Fee (₹2,000)", 2000, "Completed", "TXN-CARD-48210344", "Debit Card", "2026-09-15"),
            ("SM-2026-7310", "Vignesh M.", "Registration Fee (₹2,000)", 2000, "Completed", "TXN-UPI-74198213", "UPI (PhonePe)", "2026-09-18"),
            ("SM-2026-6190", "Karthik S.", "Registration Fee (₹2,000)", 2000, "Completed", "TXN-NETB-31094821", "Net Banking", "2026-09-20"),
            ("SM-2026-5421", "Meenakshi V.", "Registration Fee (₹2,000)", 2000, "Completed", "TXN-UPI-88421099", "UPI (Paytm)", "2026-09-22"),
            ("SM-2026-4832", "Saravanan K.", "Registration Fee (₹2,000)", 2000, "Completed", "TXN-CARD-11928401", "Credit Card", "2026-09-25"),
            ("SM-2026-3105", "Deepa N.", "Registration Fee (₹2,000)", 2000, "Completed", "TXN-UPI-55219084", "UPI (GPay)", "2026-09-28"),
            ("SM-2026-2240", "Aravindhan B.", "Registration Fee (₹2,000)", 2000, "Completed", "TXN-NETB-77210943", "Net Banking", "2026-10-01"),
            ("SM-2026-1055", "Kavitha M.", "Registration Fee (₹2,000)", 2000, "Completed", "TXN-UPI-66120944", "UPI (GPay)", "2026-10-05"),
            ("SM-FIX-0012", "Sundar & Revathi", "Match Finalisation (₹25,000)", 25000, "Completed", "TXN-BANK-FINAL-001", "Direct Bank Transfer", "2026-09-24"),
            ("SM-FIX-0013", "Muthukumar & Radhika", "Match Finalisation (₹25,000)", 25000, "Completed", "TXN-BANK-FINAL-002", "Office Cheque", "2026-10-02")
        ]
        c.executemany("""
        INSERT INTO payments (profile_id, profile_name, payment_type, amount, status, txn_id, method, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_payments)

        # Seed enquiries
        seed_enquiries = [
            ("Sundararajan M.", "9842155019", "Looking for Mudaliar bride for my son working in Bangalore. Please arrange Jathagam Porutham check.", "Kanchipuram", "New", "2026-10-04"),
            ("Ramanathan Pillai", "9443219088", "We visited your Aaladi Pilliyar Koil St office on Friday. Wanted to verify profiles in Chengalpattu district.", "Chengalpattu", "In Progress", "2026-10-05"),
            ("Kalyani Viswanathan", "9940188234", "Enquiry regarding Vadama Iyer alliances with Swathi or Hastham nakshatras.", "Chennai", "Contacted", "2026-10-06")
        ]
        c.executemany("""
        INSERT INTO enquiries (name, phone, message, district, status, date)
        VALUES (?, ?, ?, ?, ?, ?)
        """, seed_enquiries)

        # Seed activity logs
        seed_logs = [
            ("admin@sarvamangala.com", "System Setup", "SYSTEM", "Sarvamangala Matrimony secure admin portal initialized", "127.0.0.1"),
            ("admin@sarvamangala.com", "Profile Verified", "SM-2026-9214", "Priya S. verified and approved on portal", "127.0.0.1"),
            ("admin@sarvamangala.com", "Match Finalised", "SM-FIX-0012", "Sundar & Revathi alliance fixed. ₹25,000 service fee confirmed.", "127.0.0.1"),
            ("admin@sarvamangala.com", "Payment Verified", "SM-2026-1055", "Kavitha M. ₹2,000 registration fee confirmed via UPI", "127.0.0.1")
        ]
        c.executemany("""
        INSERT INTO activity_logs (admin_email, action, target_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?)
        """, seed_logs)

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

# Helper: Verify Session Token
def verify_admin_session(token: str) -> dict:
    if not token:
        return None
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
        SELECT user_id, email, role, expires_at FROM sessions
        WHERE token = ? AND role = 'admin'
        """, (token,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        user_id, email, role, expires_at = row
        # check expiry
        exp = datetime.fromisoformat(expires_at)
        if exp < datetime.now():
            return None
        return {"user_id": user_id, "email": email, "role": role}
    except Exception as e:
        print(f"Session verify error: {e}")
        return None

# ==============================================================================
# Custom Request Handler
# ==============================================================================
class MatrimonyServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def extract_token(self) -> str:
        # Check Authorization header: Bearer <token>
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()
        # Check Cookie header: sm_admin_session=<token>
        cookie_header = self.headers.get("Cookie", "")
        for item in cookie_header.split(";"):
            item = item.strip()
            if item.startswith("sm_admin_session="):
                return item.split("=", 1)[1].strip()
        return ""

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def send_unauthorized(self, message="Access Denied: Admin authorization required"):
        self.send_json({"error": message, "authenticated": False, "role": None}, status=403)

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

        # 2. API Endpoints
        if clean_path.startswith("/api/admin/"):
            token = self.extract_token()
            user = verify_admin_session(token)

            # Session check endpoint allows unauthenticated check
            if clean_path == "/api/admin/session":
                if user:
                    self.send_json({"authenticated": True, "user": user})
                else:
                    self.send_json({"authenticated": False, "user": None})
                return

            # All other /api/admin/* endpoints strictly require admin role on the server!
            if not user:
                self.send_unauthorized()
                return

            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Dashboard stats
            if clean_path == "/api/admin/stats":
                c.execute("SELECT COUNT(*) FROM profiles")
                total_members = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM profiles WHERE status = 'pending'")
                pending_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM profiles WHERE status = 'approved'")
                approved_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM profiles WHERE status = 'rejected'")
                rejected_count = c.fetchone()[0]
                c.execute("SELECT SUM(amount) FROM payments WHERE payment_type LIKE '%Registration%'")
                reg_fees = c.fetchone()[0] or 0
                c.execute("SELECT SUM(amount) FROM payments WHERE payment_type LIKE '%Finalisation%'")
                final_fees = c.fetchone()[0] or 0
                c.execute("SELECT COUNT(*) FROM enquiries WHERE status = 'New'")
                new_enquiries = c.fetchone()[0]
                conn.close()

                self.send_json({
                    "total_members": total_members,
                    "pending_approvals": pending_count,
                    "approved_profiles": approved_count,
                    "rejected_profiles": rejected_count,
                    "registration_revenue": reg_fees,
                    "finalisation_revenue": final_fees,
                    "total_revenue": reg_fees + final_fees,
                    "new_enquiries": new_enquiries
                })
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
                    like_str = f"%{search}%"
                    params.extend([like_str, like_str, like_str, like_str])
                query += " ORDER BY reg_date DESC"

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

            # Horoscope details (Authorized)
            elif clean_path.startswith("/api/admin/horoscope/"):
                pid = clean_path.split("/")[-1]
                c.execute("""
                SELECT id, name, gender, age, caste, rasi, nakshatra, lagnam,
                       birth_date, birth_time, birth_place, dosham, jathagam_doc
                FROM profiles WHERE id = ?
                """, (pid,))
                row = c.fetchone()
                conn.close()
                if row:
                    self.send_json({"horoscope": dict(row)})
                else:
                    self.send_json({"error": "Profile not found"}, status=404)
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
        post_data = self.rfile.read(content_length)

        data = {}
        if post_data:
            try:
                data = json.loads(post_data.decode("utf-8"))
            except Exception:
                pass

        # 1. Admin Login
        if clean_path == "/api/admin/login":
            email = data.get("email", "").strip()
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
                log_activity(email or "UNKNOWN", "Failed Login Attempt", "AUTH", "Invalid credentials entered", self.client_address[0])
                self.send_json({"success": False, "error": "Invalid admin email or password"}, status=401)
                return

            user_id, name, _, _, role = row

            if role != "admin":
                conn.close()
                self.send_json({"success": False, "error": "Access Denied: Account lacks admin role"}, status=403)
                return

            # Generate secure session token
            token = secrets.token_hex(32)
            expires_at = (datetime.now() + timedelta(hours=24)).isoformat()

            c.execute("""
            INSERT INTO sessions (token, user_id, email, role, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """, (token, user_id, email, role, expires_at))
            conn.commit()
            conn.close()

            log_activity(email, "Admin Login", f"USER-{user_id}", f"Admin {name} logged in successfully", self.client_address[0])

            # Send response with cookie
            body = json.dumps({
                "success": True,
                "token": token,
                "user": {"email": email, "name": name, "role": role}
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Set-Cookie", f"sm_admin_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.end_headers()
            self.wfile.write(body)
            return

        # 2. Admin Logout
        elif clean_path == "/api/admin/logout":
            token = self.extract_token()
            user = verify_admin_session(token)
            if user:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
                conn.close()
                log_activity(user["email"], "Admin Logout", f"TOKEN-{token[:8]}", "Admin logged out and session destroyed", self.client_address[0])

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Set-Cookie", "sm_admin_session=deleted; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Logged out successfully"}).encode("utf-8"))
            return

        # 3. Protected Admin Actions: strictly enforce admin role!
        if clean_path.startswith("/api/admin/"):
            token = self.extract_token()
            user = verify_admin_session(token)
            if not user:
                self.send_unauthorized()
                return

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            # Member Action: approve, reject, correction, suspend, block, delete
            if clean_path == "/api/admin/member-action":
                pid = data.get("id")
                action = data.get("action")
                notes = data.get("notes", "")

                if not pid or not action:
                    conn.close()
                    self.send_json({"error": "Profile ID and action required"}, status=400)
                    return

                if action == "approve":
                    c.execute("UPDATE profiles SET status = 'approved', is_approved = 1, notes = ? WHERE id = ?", (notes, pid))
                    log_activity(user["email"], "Profile Approved", pid, f"Approved profile {pid}. Notes: {notes}", self.client_address[0])
                elif action == "reject":
                    c.execute("UPDATE profiles SET status = 'rejected', is_approved = 0, notes = ? WHERE id = ?", (notes, pid))
                    log_activity(user["email"], "Profile Rejected", pid, f"Rejected profile {pid}. Reason: {notes}", self.client_address[0])
                elif action == "suspend":
                    c.execute("UPDATE profiles SET status = 'suspended', is_approved = 0, notes = ? WHERE id = ?", (notes, pid))
                    log_activity(user["email"], "Profile Suspended", pid, f"Suspended profile {pid}", self.client_address[0])
                elif action == "block":
                    c.execute("UPDATE profiles SET status = 'blocked', is_approved = 0, notes = ? WHERE id = ?", (notes, pid))
                    log_activity(user["email"], "Profile Blocked", pid, f"Blocked/Blacklisted profile {pid}", self.client_address[0])
                elif action == "correction":
                    c.execute("UPDATE profiles SET status = 'correction_requested', is_approved = 0, notes = ? WHERE id = ?", (notes, pid))
                    log_activity(user["email"], "Correction Requested", pid, f"Requested correction for {pid}: {notes}", self.client_address[0])
                elif action == "delete":
                    c.execute("DELETE FROM profiles WHERE id = ?", (pid,))
                    log_activity(user["email"], "Profile Deleted", pid, f"Deleted profile {pid} permanently", self.client_address[0])

                conn.commit()
                conn.close()
                self.send_json({"success": True, "action": action, "id": pid})
                return

            # Edit Profile
            elif clean_path == "/api/admin/edit-profile":
                pid = data.get("id")
                if not pid:
                    conn.close()
                    self.send_json({"error": "Profile ID required"}, status=400)
                    return
                c.execute("""
                UPDATE profiles SET
                    name = ?, age = ?, caste = ?, subcaste = ?, district = ?, city = ?,
                    education = ?, occupation = ?, income = ?, partner_pref = ?, notes = ?
                WHERE id = ?
                """, (
                    data.get("name"), data.get("age"), data.get("caste"), data.get("subcaste"),
                    data.get("district"), data.get("city"), data.get("education"),
                    data.get("occupation"), data.get("income"), data.get("partner_pref"),
                    data.get("notes"), pid
                ))
                conn.commit()
                conn.close()
                log_activity(user["email"], "Profile Edited", pid, f"Updated profile details for {pid}", self.client_address[0])
                self.send_json({"success": True, "id": pid})
                return

            # Record Manual Payment / Finalisation Fee
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

            # Change Admin Password
            elif clean_path == "/api/admin/change-password":
                current_pw = data.get("current_password")
                new_pw = data.get("new_password")
                c.execute("SELECT password_hash, salt FROM admin_users WHERE email = ?", (user["email"],))
                row = c.fetchone()
                if not row or not verify_password(current_pw, row[0], row[1]):
                    conn.close()
                    self.send_json({"error": "Current password is incorrect"}, status=400)
                    return
                new_hash, new_salt = hash_password(new_pw)
                c.execute("UPDATE admin_users SET password_hash = ?, salt = ? WHERE email = ?", (new_hash, new_salt, user["email"]))
                conn.commit()
                conn.close()
                log_activity(user["email"], "Password Changed", "SECURITY", "Admin password changed successfully", self.client_address[0])
                self.send_json({"success": True, "message": "Password updated successfully"})
                return

            conn.close()
            self.send_json({"error": "Unknown admin POST endpoint"}, status=404)
            return

        # 4. Public Endpoints: Contact Form Enquiry
        if clean_path == "/api/public/enquiry":
            name = data.get("name", "").strip()
            phone = data.get("phone", "").strip()
            msg = data.get("message", "").strip()
            if name and phone:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("""
                INSERT INTO enquiries (name, phone, message, district, status, date)
                VALUES (?, ?, ?, 'Kanchipuram', 'New', ?)
                """, (name, phone, msg, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                self.send_json({"success": True, "message": "Enquiry received. Kanchipuram office will call shortly."})
                return
            self.send_json({"error": "Name and phone required"}, status=400)
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
        print(f"===============================================================", flush=True)
        print(f" Sarvamangala Matrimony Server running at http://0.0.0.0:{PORT}", flush=True)
        print(f" Public Website: http://0.0.0.0:{PORT}/index.html", flush=True)
        print(f" Private Hidden Admin URL: http://0.0.0.0:{PORT}/sm-admin", flush=True)
        print(f"===============================================================", flush=True)
        httpd.serve_forever()
