from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class RegistrationPayment(models.Model):
    """
    Tracks the mandatory ₹2,000 one-time registration fee via Google Pay (GPay).
    Payee Mobile: 9942006877 | UPI: 9942006877@upi.
    Admin must approve before member profile and account can be activated.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PAYMENT_SUBMITTED', 'UTR Submitted / Verification Awaiting'),
        ('PAID', 'Verified & Paid (Account Active)'),
        ('REJECTED', 'Payment Rejected / Invalid UTR'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registration_payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=2000.00)
    payee_mobile = models.CharField(max_length=20, default='9942006877')
    upi_id = models.CharField(max_length=50, default='9942006877@upi')
    transaction_ref = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    receipt_no = models.CharField(max_length=64, blank=True, null=True, unique=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - ₹{self.amount} ({self.status}) - UTR: {self.transaction_ref or 'N/A'}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'GPay ₹2,000 Registration Payment'
        verbose_name_plural = 'GPay ₹2,000 Registration Payments'


class Profile(models.Model):
    """
    Matrimonial candidate profile with personal, astrological, educational, and contact details.
    """
    GENDER_CHOICES = [
        ('M', 'Groom (மணமகன்)'),
        ('F', 'Bride (மணமகள்)'),
    ]

    MARITAL_CHOICES = [
        ('Never Married', 'Never Married'),
        ('Widowed', 'Widowed'),
        ('Divorced', 'Divorced'),
        ('Awaiting Divorce', 'Awaiting Divorce'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_id = models.CharField(max_length=20, unique=True, db_index=True)
    full_name = models.CharField(max_length=120)
    gender = models.CharField(max_length=5, choices=GENDER_CHOICES)
    dob = models.DateField()
    age = models.PositiveIntegerField()
    marital_status = models.CharField(max_length=30, choices=MARITAL_CHOICES, default='Never Married')
    religion = models.CharField(max_length=50, default='Hindu')
    caste = models.CharField(max_length=80)
    sub_caste = models.CharField(max_length=80, blank=True)
    gothram = models.CharField(max_length=60, blank=True)
    star_nakshatram = models.CharField(max_length=60)
    rasi = models.CharField(max_length=60)
    dosham = models.CharField(max_length=50, default='No Dosham')
    height_cm = models.PositiveIntegerField(default=165)
    education = models.CharField(max_length=100)
    education_detail = models.CharField(max_length=150, blank=True)
    occupation = models.CharField(max_length=100)
    employed_in = models.CharField(max_length=60, default='Private')
    annual_income = models.CharField(max_length=60)
    city = models.CharField(max_length=60)
    district = models.CharField(max_length=60, default='Kanchipuram')
    state = models.CharField(max_length=60, default='Tamil Nadu')
    country = models.CharField(max_length=60, default='India')
    about_me = models.TextField(blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    photo_url = models.CharField(max_length=255, blank=True)
    horoscope_chart = models.FileField(upload_to='horoscopes/', blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_visible = models.BooleanField(default=True)
    match_score = models.PositiveIntegerField(default=92)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.profile_id} - {self.full_name} ({self.get_gender_display()}) - {self.district}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gender', 'age']),
            models.Index(fields=['district', 'caste']),
            models.Index(fields=['is_approved', 'is_visible']),
        ]


class FamilyDetails(models.Model):
    """
    Detailed family background for traditional matrimonial matchmaking.
    """
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='family')
    father_name = models.CharField(max_length=100)
    father_occupation = models.CharField(max_length=100, blank=True)
    mother_name = models.CharField(max_length=100)
    mother_occupation = models.CharField(max_length=100, blank=True)
    brothers_count = models.PositiveIntegerField(default=0)
    brothers_married = models.PositiveIntegerField(default=0)
    sisters_count = models.PositiveIntegerField(default=0)
    sisters_married = models.PositiveIntegerField(default=0)
    family_values = models.CharField(max_length=50, default='Traditional')
    family_type = models.CharField(max_length=50, default='Nuclear')
    family_status = models.CharField(max_length=50, default='Upper Middle Class')
    native_place = models.CharField(max_length=100, default='Kanchipuram')

    def __str__(self):
        return f"Family of {self.profile.profile_id} ({self.father_name})"


class PartnerPreference(models.Model):
    """
    Desired partner preferences for automated scoring and Priya Matching.
    """
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='preference')
    age_min = models.PositiveIntegerField(default=21)
    age_max = models.PositiveIntegerField(default=32)
    height_min_cm = models.PositiveIntegerField(default=150)
    height_max_cm = models.PositiveIntegerField(default=185)
    marital_status = models.CharField(max_length=50, default='Never Married')
    religion = models.CharField(max_length=50, default='Hindu')
    caste = models.CharField(max_length=80, blank=True)
    education = models.CharField(max_length=100, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    preferred_district = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Preferences of {self.profile.profile_id} (Age {self.age_min}-{self.age_max})"


class Interest(models.Model):
    """
    Formal interest sent between candidate profiles.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('WITHDRAWN', 'Withdrawn'),
    ]

    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='interests_sent')
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='interests_received')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.profile_id} -> {self.receiver.profile_id} [{self.status}]"


class Shortlist(models.Model):
    """
    Bookmarked profiles saved by a candidate.
    """
    user_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='shortlists')
    shortlisted_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='shortlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_profile', 'shortlisted_profile')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user_profile.profile_id} bookmarked {self.shortlisted_profile.profile_id}"


class ContactRequest(models.Model):
    """
    Request to reveal private phone number & horoscope.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved & Revealed'),
        ('REJECTED', 'Rejected'),
    ]

    requester = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='contact_requests_made')
    target = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='contact_requests_received')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('requester', 'target')
        ordering = ['-requested_at']

    def __str__(self):
        return f"Contact: {self.requester.profile_id} requested {self.target.profile_id} ({self.status})"


class Notification(models.Model):
    """
    User in-app notifications for interest updates, profile approvals, and messages.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{'READ' if self.is_read else 'UNREAD'}] {self.user.username}: {self.title}"


class MembershipPlan(models.Model):
    """
    Available membership tiers: Free, Silver Alliance, Gold Vivaham, Diamond Heritage.
    """
    plan_code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    validity_days = models.PositiveIntegerField()
    contact_limit = models.PositiveIntegerField()
    features = models.JSONField(default=list)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ₹{self.price} ({self.validity_days} days)"


class UserMembership(models.Model):
    """
    Active membership subscription tied to an approved user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    plan = models.ForeignKey(MembershipPlan, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    contacts_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} (Valid till {self.end_date})"


class Enquiry(models.Model):
    """
    Public contact form submissions and assistance enquiries.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    subject = models.CharField(max_length=150)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Enquiries'

    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.subject}"


class ProfileReport(models.Model):
    """
    User reports against inappropriate profiles or fraudulent accounts.
    """
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reported_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=30, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report on {self.reported_profile.profile_id} by {self.reporter or 'Anonymous'}"


class SuccessStory(models.Model):
    """
    Verified Hindu marriage success stories from Kanchipuram and Tamil Nadu.
    """
    couple_names = models.CharField(max_length=150)
    wedding_date = models.CharField(max_length=60)
    story = models.TextField()
    photo_url = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Success Stories'

    def __str__(self):
        return f"{self.couple_names} ({self.wedding_date})"


class Testimonial(models.Model):
    """
    Authentic client reviews from parents and newly married couples.
    """
    reviewer_name = models.CharField(max_length=100)
    relation = models.CharField(max_length=80)
    city = models.CharField(max_length=60, default='Kanchipuram')
    rating = models.PositiveIntegerField(default=5)
    review_text = models.TextField()
    photo_url = models.CharField(max_length=255, blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reviewer_name} ({self.city}) - {self.rating}★"


class ActivityAuditLog(models.Model):
    """
    Security audit trails for admin operations, verification decisions, and logins.
    """
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=60, blank=True)
    target_id = models.CharField(max_length=60, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.actor or 'System'}: {self.action}"
