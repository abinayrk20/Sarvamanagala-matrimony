import re

server_path = "server.py"
with open(server_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Replace /api/matches implementation in do_GET
old_matches_pattern = r'# 4\. Search & Matches Endpoint \(Approved profiles only\)\s+elif clean_path == "/api/matches":.+?(?=# 5\. Profile Details Endpoint)'
new_matches_code = '''# 4. Search & Matches Endpoint (Approved profiles only)
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

        '''

code = re.sub(old_matches_pattern, new_matches_code, code, flags=re.DOTALL)
print("[OK] Replaced /api/matches with timeline filter & privacy mask")

# 2. Replace /api/profile/<pid> implementation in do_GET
old_profile_pattern = r'# 5\. Profile Details Endpoint\s+elif clean_path\.startswith\("/api/profile/"\):.+?(?=# 6\. User Interests Endpoint)'
new_profile_code = '''# 5. Profile Details Endpoint
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

        '''

code = re.sub(old_profile_pattern, new_profile_code, code, flags=re.DOTALL)
print("[OK] Replaced /api/profile/<pid> with privacy & like/mutual states")

# 3. Add GET endpoints for secret likes, icebreakers, privacy settings, admin trust badges
get_extra_routes = '''        # 6b. Secret Likes: Mutual Matches Endpoint
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
            mutual_matches = [apply_privacy_mask(dict(r), user, c) for r in c.fetchall()]
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
                self.send_json({"photo_privacy": "members_only", "phone_privacy": "consent_only", "horoscope_privacy": "members_only", "trust_badge_status": "pending"})
                return
            self.send_json(dict(row))
            return
'''

shortlist_marker = '# 7. User Shortlist Endpoint'
if '/api/secret-likes/mutual' not in code:
    code = code.replace(shortlist_marker, get_extra_routes + '\n        ' + shortlist_marker, 1)
    print("[OK] Added GET routes: /api/secret-likes/mutual, /api/icebreakers, /api/settings/privacy")

# 4. In admin endpoints (do_GET), add /api/admin/trust-badges
admin_badges_code = '''            # Kanchi Silk Trust Badges Queue
            elif clean_path == "/api/admin/trust-badges":
                c.execute("""
                SELECT id, name, gender, age, district, phone, trust_badge_status, trust_badge_doc, trust_badge_verified_at, trust_badge_verified_by
                FROM profiles
                ORDER BY CASE WHEN trust_badge_status = 'pending' THEN 0 ELSE 1 END, id ASC
                """)
                badges = [dict(r) for r in c.fetchall()]
                conn.close()
                self.send_json({"badges": badges})
                return
'''

stats_marker = '# Dashboard stats\n            if clean_path == "/api/admin/stats":'
if '/api/admin/trust-badges' not in code:
    code = code.replace(stats_marker, admin_badges_code + '\n            ' + stats_marker, 1)
    print("[OK] Added GET /api/admin/trust-badges")

# 5. Update Registration in do_POST: Unique Profile ID SMK-2026-XXXXXX and marriage_timeline
reg_target_old = r'# Create Profile Record \(Status: pending\)\s+profile_id = f"SM-2026-\{secrets\.randbelow\(8999\) \+ 1000\}"\s+subcaste = data\.get\("sub_caste", ""\)\.strip\(\)\s+photo_url = data\.get\("photo_url", ""\)\.strip\(\)'
reg_target_new = '''# Create Profile Record (Status: pending) with sequential unique SMK-2026-XXXXXX ID
            profile_id = generate_unique_profile_id(c, 2026)
            subcaste = data.get("sub_caste", "").strip()
            marriage_timeline = data.get("marriage_timeline", "Flexible").strip()
            photo_url = data.get("photo_url", "").strip()'''

code = re.sub(reg_target_old, reg_target_new, code)

# Update the INSERT INTO profiles in registration
insert_old = r'INSERT INTO profiles \(\s+id, user_id, name, gender, age, religion, caste, subcaste, district,\s+education, occupation, photo_url, phone, email, is_approved, status\s+\)\s+VALUES \(\?, \?, \?, \?, \?, \'Hindu\', \?, \?, \?, \?, \?, \?, \?, \?, 0, \'pending\'\)'
insert_new = '''INSERT INTO profiles (
                id, user_id, name, gender, age, religion, caste, subcaste, district,
                education, occupation, photo_url, phone, email, is_approved, status,
                marriage_timeline, trust_badge_status, photo_privacy, phone_privacy, horoscope_privacy
            )
            VALUES (?, ?, ?, ?, ?, 'Hindu', ?, ?, ?, ?, ?, ?, ?, ?, 0, 'pending', ?, 'pending', 'members_only', 'consent_only', 'members_only')'''

code = re.sub(insert_old, insert_new, code)

# Update params tuple for registration INSERT
old_params = r'profile_id, user_id, name, gender, age, caste, subcaste, district,\s+education, occupation, photo_url, phone, email\s+\)\)'
new_params = '''profile_id, user_id, name, gender, age, caste, subcaste, district,
                education, occupation, photo_url, phone, email, marriage_timeline
            ))'''
code = re.sub(old_params, new_params, code)
print("[OK] Updated registration endpoint for unique SMK ID and marriage timeline")

# 6. Add POST endpoints: secret-likes/toggle, shortlist/remove, interests/withdraw, settings/privacy, apply-trust-badge, icebreakers/send, icebreakers/reply
post_extra_routes = '''        # 8b. SECRET LIKES TOGGLE & MUTUAL MATCHING
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
'''

toggle_shortlist_marker = '# 11. SHORTLIST TOGGLE'
if '/api/secret-likes/toggle' not in code:
    code = code.replace(toggle_shortlist_marker, post_extra_routes + '\n        ' + toggle_shortlist_marker, 1)
    print("[OK] Added POST endpoints: /api/secret-likes/toggle, /api/shortlist/remove, /api/interests/withdraw, /api/settings/privacy, /api/profile/apply-trust-badge, /api/icebreakers/send, /api/icebreakers/reply")

# 7. Add admin action for verifying Kanchi Silk Trust badge
admin_trust_action = '''            # Kanchi Silk Trust Badge Verification: approve or reject
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
'''

member_action_marker = '# Member Action: approve, reject, suspend, reactivate, delete'
if '/api/admin/verify-trust-badge' not in code:
    code = code.replace(member_action_marker, admin_trust_action + '\n            ' + member_action_marker, 1)
    print("[OK] Added admin POST /api/admin/verify-trust-badge")

with open(server_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Finished updating server routes!")
