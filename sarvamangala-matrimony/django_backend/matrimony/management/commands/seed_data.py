import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from matrimony.models import (
    MembershipPlan, SuccessStory, Testimonial, Profile,
    FamilyDetails, PartnerPreference, RegistrationPayment
)

class Command(BaseCommand):
    help = 'Seeds initial membership plans, success stories, testimonials, and verified profiles'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Sarvamangala Matrimony database...")

        # 1. Superuser / Admin
        admin_user, created = User.objects.get_or_create(
            username='admin@sarvamangala.com',
            defaults={
                'email': 'admin@sarvamangala.com',
                'first_name': 'Kanchipuram',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            admin_user.set_password('KanchiMangala@2026')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin@sarvamangala.com"))

        # 2. Membership Plans
        plans_data = [
            {
                "plan_code": "free",
                "name": "Free Registration",
                "price": 0,
                "validity_days": 30,
                "contact_limit": 2,
                "features": [
                    "Browse verified Hindu profiles",
                    "Basic horoscope match calculation",
                    "Send up to 2 interests per month",
                    "Standard customer helpline"
                ],
                "is_popular": False
            },
            {
                "plan_code": "silver",
                "name": "Silver Alliance",
                "price": 3500,
                "validity_days": 90,
                "contact_limit": 25,
                "features": [
                    "Direct contact view for 25 verified profiles",
                    "Full 10 Porutham astrology breakdown",
                    "Unlimited interest requests",
                    "Verified profile badge",
                    "Priority WhatsApp support"
                ],
                "is_popular": False
            },
            {
                "plan_code": "gold",
                "name": "Gold Vivaham",
                "price": 6500,
                "validity_days": 180,
                "contact_limit": 60,
                "features": [
                    "Direct contact view for 60 verified profiles",
                    "Personal Kanchipuram relationship manager",
                    "Horoscope matching assistance",
                    "Profile highlighted in search results",
                    "Direct family coordination"
                ],
                "is_popular": True
            },
            {
                "plan_code": "diamond",
                "name": "Diamond Heritage",
                "price": 12000,
                "validity_days": 365,
                "contact_limit": 150,
                "features": [
                    "Unlimited verified contact reveals",
                    "Dedicated Senior Astrologer consultation",
                    "Executive home visit in Tamil Nadu",
                    "Guaranteed family meetings arranged",
                    "VIP matchmaking until wedding fixed"
                ],
                "is_popular": False
            }
        ]

        for p in plans_data:
            MembershipPlan.objects.update_or_create(
                plan_code=p["plan_code"],
                defaults=p
            )
        self.stdout.write(self.style.SUCCESS("Seeded 4 Membership Plans."))

        # 3. Success Stories
        stories_data = [
            {
                "couple_names": "Karthikeyan & Soundarya",
                "wedding_date": "Married Feb 2026 • Kanchipuram",
                "story": "We found each other through Sarvamangala Matrimony within three months. Both families are from Kanchipuram, and our horoscopes matched with 9.5 Poruthams. The team arranged our first meeting at Sri Varadaraja Perumal Temple with utmost grace and dignity.",
                "photo_url": "https://images.unsplash.com/photo-1583939003579-730e3918a45a?auto=format&fit=crop&w=400&q=80"
            },
            {
                "couple_names": "Dr. Vignesh & Dr. Priya",
                "wedding_date": "Married Jan 2026 • Chennai",
                "story": "As practicing physicians, our schedules were hectic. Sarvamangala Matrimony's dedicated relationship manager filtered profiles strictly according to our community values and educational expectations. Truly grateful for this blessing.",
                "photo_url": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=400&q=80"
            },
            {
                "couple_names": "Arun Kumar & Divyabharathi",
                "wedding_date": "Married Nov 2025 • Vellore",
                "story": "The transparent verification process and authentic family backgrounds gave my parents immense confidence. Today we are happily united with the blessings of Kanchi Kamakshi Amman.",
                "photo_url": "https://images.unsplash.com/photo-1511285560929-80b456fea0bc?auto=format&fit=crop&w=400&q=80"
            },
            {
                "couple_names": "Suresh & Keerthana",
                "wedding_date": "Married Oct 2025 • Tiruvannamalai",
                "story": "From horoscope matching to family background inquiries, everything was conducted with utmost respect and cultural authenticity. Highly recommended for Tamil Hindu families.",
                "photo_url": "https://images.unsplash.com/photo-1606800052052-a08af7148866?auto=format&fit=crop&w=400&q=80"
            }
        ]

        for s in stories_data:
            SuccessStory.objects.update_or_create(
                couple_names=s["couple_names"],
                defaults=s
            )
        self.stdout.write(self.style.SUCCESS("Seeded 4 Success Stories."))

        # 4. Testimonials
        testimonials_data = [
            {
                "reviewer_name": "R. Natarajan",
                "relation": "Father of the Bride",
                "city": "Kanchipuram",
                "rating": 5,
                "review_text": "Sarvamangala Matrimony provided exceptionally genuine matches for my elder daughter. The staff personally verified the groom's family background. We conducted the wedding at Kanchi Sri Ekambareswarar Temple with immense joy.",
                "photo_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=150&q=80"
            },
            {
                "reviewer_name": "S. Meenakshi Sundaram",
                "relation": "Groom's Mother",
                "city": "Chennai",
                "rating": 5,
                "review_text": "In today's digital world, finding a matrimony service that values orthodox Vedic tradition and family dignity is rare. Sarvamangala Matrimony is by far the most authentic service in Tamil Nadu.",
                "photo_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=150&q=80"
            },
            {
                "reviewer_name": "K. Venkatesan",
                "relation": "Father of the Groom",
                "city": "Chengalpattu",
                "rating": 5,
                "review_text": "The ₹2,000 registration fee guarantees that only serious, committed families are registered. No fake profiles or spam calls. We found our daughter-in-law within 45 days.",
                "photo_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=150&q=80"
            },
            {
                "reviewer_name": "B. Sivakumar",
                "relation": "Father of the Bride",
                "city": "Vellore",
                "rating": 5,
                "review_text": "Their horoscope analysis and Porutham evaluation by experienced Vedic astrologers was extremely accurate. Very trustworthy customer service on both helpline numbers.",
                "photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80"
            }
        ]

        for t in testimonials_data:
            Testimonial.objects.update_or_create(
                reviewer_name=t["reviewer_name"],
                defaults=t
            )
        self.stdout.write(self.style.SUCCESS("Seeded 4 Testimonials."))

        # 5. Seed Verified Sample Profiles
        profiles_data = [
            {
                "email": "priya.natarajan@example.com",
                "profile_id": "SM-10821",
                "full_name": "Priya Natarajan",
                "gender": "F",
                "dob": datetime.date(1998, 5, 14),
                "age": 28,
                "caste": "Mudaliar",
                "sub_caste": "Agamudayar",
                "star_nakshatram": "Rohini",
                "rasi": "Rishabam",
                "education": "M.Tech (Software Systems)",
                "occupation": "Senior Cloud Architect",
                "annual_income": "₹18,00,000",
                "district": "Kanchipuram",
                "city": "Kanchipuram",
                "phone": "9840123456",
                "photo_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80"
            },
            {
                "email": "ananya.sundaram@example.com",
                "profile_id": "SM-10822",
                "full_name": "Ananya Sundaram",
                "gender": "F",
                "dob": datetime.date(2000, 8, 22),
                "age": 26,
                "caste": "Brahmin - Iyer",
                "sub_caste": "Vadama",
                "star_nakshatram": "Swati",
                "rasi": "Thulam",
                "education": "B.E. (Computer Science)",
                "occupation": "Senior UI/UX Specialist",
                "annual_income": "₹14,50,000",
                "district": "Chennai",
                "city": "Chennai",
                "phone": "9840234567",
                "photo_url": "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=400&q=80"
            },
            {
                "email": "karthik.subramanian@example.com",
                "profile_id": "SM-10823",
                "full_name": "Karthik Subramanian",
                "gender": "M",
                "dob": datetime.date(1996, 2, 10),
                "age": 30,
                "caste": "Pillai",
                "sub_caste": "Saiva Pillai",
                "star_nakshatram": "Anusham",
                "rasi": "Viruchigam",
                "education": "M.S. Data Science",
                "occupation": "Lead AI Engineer",
                "annual_income": "₹24,00,000",
                "district": "Kanchipuram",
                "city": "Kanchipuram",
                "phone": "9840345678",
                "photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80"
            },
            {
                "email": "dr.saravanan@example.com",
                "profile_id": "SM-10824",
                "full_name": "Dr. Saravanan Ramanathan",
                "gender": "M",
                "dob": datetime.date(1994, 11, 4),
                "age": 32,
                "caste": "Chettiar",
                "sub_caste": "Vaniya Chettiar",
                "star_nakshatram": "Revathi",
                "rasi": "Meenam",
                "education": "M.D. (General Medicine)",
                "occupation": "Consultant Physician",
                "annual_income": "₹22,00,000",
                "district": "Vellore",
                "city": "Vellore",
                "phone": "9840456789",
                "photo_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=400&q=80"
            }
        ]

        for pd in profiles_data:
            user, u_created = User.objects.get_or_create(
                username=pd["email"],
                defaults={
                    "email": pd["email"],
                    "first_name": pd["full_name"].split()[0],
                    "is_active": True
                }
            )
            if u_created:
                user.set_password("MatrimonyPass@2026")
                user.save()

            profile, _ = Profile.objects.update_or_create(
                user=user,
                defaults={
                    "profile_id": pd["profile_id"],
                    "full_name": pd["full_name"],
                    "gender": pd["gender"],
                    "dob": pd["dob"],
                    "age": pd["age"],
                    "caste": pd["caste"],
                    "sub_caste": pd["sub_caste"],
                    "star_nakshatram": pd["star_nakshatram"],
                    "rasi": pd["rasi"],
                    "education": pd["education"],
                    "occupation": pd["occupation"],
                    "annual_income": pd["annual_income"],
                    "district": pd["district"],
                    "city": pd["city"],
                    "phone": pd["phone"],
                    "email": pd["email"],
                    "photo_url": pd["photo_url"],
                    "is_approved": True,
                    "is_active": True,
                    "is_visible": True,
                }
            )

            RegistrationPayment.objects.update_or_create(
                user=user,
                defaults={
                    "amount": 2000.00,
                    "payee_mobile": "9942006877",
                    "upi_id": "9942006877@upi",
                    "transaction_ref": f"UPI2026{user.id}998811",
                    "receipt_no": f"RCP-2026-{1000 + user.id}",
                    "status": "PAID",
                    "submitted_at": timezone.now(),
                    "verified_at": timezone.now(),
                    "admin_notes": "Verified against bank records."
                }
            )

            FamilyDetails.objects.get_or_create(
                profile=profile,
                defaults={
                    "father_name": f"Mr. {pd['full_name'].split()[-1]}",
                    "father_occupation": "Business Executive",
                    "mother_name": "Mrs. Kalyani",
                    "mother_occupation": "Homemaker",
                    "native_place": pd["district"]
                }
            )

            PartnerPreference.objects.get_or_create(
                profile=profile,
                defaults={
                    "age_min": max(18, pd["age"] - 5),
                    "age_max": pd["age"] + 5,
                    "preferred_district": pd["district"]
                }
            )

        self.stdout.write(self.style.SUCCESS("Seeded verified sample profiles and verified ₹2,000 payments!"))
        self.stdout.write(self.style.SUCCESS("All seed operations finished successfully."))
