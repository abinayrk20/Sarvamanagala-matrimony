import re
from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    RegistrationPayment, Profile, FamilyDetails, PartnerPreference,
    Interest, Shortlist, ContactRequest, Notification, MembershipPlan,
    UserMembership, Enquiry, ProfileReport, SuccessStory, Testimonial, ActivityAuditLog
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']


class RegistrationPaymentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.profile.full_name', read_only=True)
    phone = serializers.CharField(source='user.profile.phone', read_only=True)
    gender = serializers.CharField(source='user.profile.gender', read_only=True)

    class Meta:
        model = RegistrationPayment
        fields = [
            'id', 'user', 'username', 'full_name', 'phone', 'gender',
            'amount', 'payee_mobile', 'upi_id', 'transaction_ref',
            'receipt_no', 'status', 'submitted_at', 'verified_at',
            'admin_notes', 'created_at'
        ]
        read_only_fields = ['id', 'amount', 'payee_mobile', 'upi_id', 'receipt_no', 'verified_at', 'created_at']


class FamilyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyDetails
        exclude = ['id', 'profile']


class PartnerPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerPreference
        exclude = ['id', 'profile']


class ProfileListSerializer(serializers.ModelSerializer):
    """
    Publicly safe profile representation for browsing & search.
    Phone number and sensitive identifiers are omitted.
    """
    class Meta:
        model = Profile
        fields = [
            'id', 'profile_id', 'full_name', 'gender', 'age', 'marital_status',
            'religion', 'caste', 'sub_caste', 'star_nakshatram', 'rasi', 'dosham',
            'height_cm', 'education', 'occupation', 'annual_income',
            'city', 'district', 'state', 'about_me', 'photo_url', 'match_score'
        ]


class ProfileDetailSerializer(serializers.ModelSerializer):
    """
    Full profile details including nested family and partner preferences.
    """
    family = FamilyDetailsSerializer(read_only=True)
    preference = PartnerPreferenceSerializer(read_only=True)
    registration_status = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = '__all__'

    def get_registration_status(self, obj):
        if hasattr(obj.user, 'registration_payment'):
            return obj.user.registration_payment.status
        return 'UNKNOWN'


class RegistrationSerializer(serializers.Serializer):
    """
    Handles member onboarding with mandatory ₹2,000 GPay registration tracking.
    Account remains PENDING until payment verification.
    """
    full_name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=8)
    gender = serializers.ChoiceField(choices=[('M', 'Groom'), ('F', 'Bride')])
    dob = serializers.DateField()
    caste = serializers.CharField(max_length=80)
    star_nakshatram = serializers.CharField(max_length=60)
    rasi = serializers.CharField(max_length=60)
    education = serializers.CharField(max_length=100)
    occupation = serializers.CharField(max_length=100)
    annual_income = serializers.CharField(max_length=60, default='₹5,00,000 - ₹8,00,000')
    district = serializers.CharField(max_length=60, default='Kanchipuram')
    city = serializers.CharField(max_length=60, default='Kanchipuram')
    height_cm = serializers.IntegerField(default=165)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return value.lower()

    def validate_phone(self, value):
        cleaned = re.sub(r'\D', '', value)
        if len(cleaned) < 10:
            raise serializers.ValidationError("Please provide a valid 10-digit mobile number.")
        if Profile.objects.filter(phone=cleaned).exists():
            raise serializers.ValidationError("This mobile number is already registered.")
        return cleaned

    def create(self, validated_data):
        # 1. Create Django User (Inactive until admin verifies ₹2,000 payment)
        username = validated_data['email']
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False
        )

        # 2. Compute Age from DOB
        dob = validated_data['dob']
        today = timezone.now().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise serializers.ValidationError({"dob": "Candidate must be at least 18 years of age."})

        # 3. Generate Profile ID (e.g. SM-10850)
        profile_count = Profile.objects.count() + 10820
        profile_id = f"SM-{profile_count}"

        # 4. Create Profile
        photo_url = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80' if validated_data['gender'] == 'F' else 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80'

        profile = Profile.objects.create(
            user=user,
            profile_id=profile_id,
            full_name=validated_data['full_name'],
            gender=validated_data['gender'],
            dob=dob,
            age=age,
            religion='Hindu',
            caste=validated_data['caste'],
            star_nakshatram=validated_data['star_nakshatram'],
            rasi=validated_data['rasi'],
            education=validated_data['education'],
            occupation=validated_data['occupation'],
            annual_income=validated_data.get('annual_income', '₹5,00,000 - ₹8,00,000'),
            district=validated_data.get('district', 'Kanchipuram'),
            city=validated_data.get('city', 'Kanchipuram'),
            height_cm=validated_data.get('height_cm', 165),
            phone=validated_data['phone'],
            email=validated_data['email'],
            photo_url=photo_url,
            is_approved=False,
            is_active=True
        )

        # 5. Create default Family Details & Preferences
        FamilyDetails.objects.create(
            profile=profile,
            father_name='Family Head',
            mother_name='Family Matron',
            native_place=validated_data.get('district', 'Kanchipuram')
        )
        PartnerPreference.objects.create(
            profile=profile,
            age_min=max(18, age - 5),
            age_max=age + 5,
            preferred_district=validated_data.get('district', 'Kanchipuram')
        )

        # 6. Create Mandatory ₹2,000 Registration Payment record (Status: PENDING)
        reg_payment = RegistrationPayment.objects.create(
            user=user,
            amount=2000.00,
            payee_mobile='9942006877',
            upi_id='9942006877@upi',
            status='PENDING'
        )

        return {
            'user': user,
            'profile': profile,
            'payment': reg_payment
        }


class PaymentSubmissionSerializer(serializers.Serializer):
    """
    Allows user to submit their 12-digit UPI / UTR Transaction ID after paying ₹2,000 via GPay.
    """
    transaction_ref = serializers.CharField(max_length=64, required=True)

    def validate_transaction_ref(self, value):
        cleaned = value.strip()
        if len(cleaned) < 8:
            raise serializers.ValidationError("Please provide a valid UTR or Transaction reference.")
        return cleaned


class InterestSerializer(serializers.ModelSerializer):
    sender_profile = ProfileListSerializer(source='sender', read_only=True)
    receiver_profile = ProfileListSerializer(source='receiver', read_only=True)

    class Meta:
        model = Interest
        fields = ['id', 'sender', 'sender_profile', 'receiver', 'receiver_profile', 'status', 'message', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']


class ShortlistSerializer(serializers.ModelSerializer):
    profile = ProfileListSerializer(source='shortlisted_profile', read_only=True)

    class Meta:
        model = Shortlist
        fields = ['id', 'user_profile', 'shortlisted_profile', 'profile', 'created_at']
        read_only_fields = ['id', 'user_profile', 'created_at']


class ContactRequestSerializer(serializers.ModelSerializer):
    requester_profile = ProfileListSerializer(source='requester', read_only=True)
    target_profile = ProfileListSerializer(source='target', read_only=True)
    target_phone = serializers.SerializerMethodField()

    class Meta:
        model = ContactRequest
        fields = ['id', 'requester', 'requester_profile', 'target', 'target_profile', 'target_phone', 'status', 'requested_at']
        read_only_fields = ['id', 'requester', 'requested_at']

    def get_target_phone(self, obj):
        # Only show target phone if approved
        if obj.status == 'APPROVED':
            return obj.target.phone
        return None


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'link', 'is_read', 'created_at']


class MembershipPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPlan
        fields = '__all__'


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = '__all__'


class ProfileReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileReport
        fields = '__all__'


class SuccessStorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SuccessStory
        fields = '__all__'


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = '__all__'


class ActivityAuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = ActivityAuditLog
        fields = ['id', 'actor', 'actor_name', 'action', 'target_type', 'target_id', 'ip_address', 'details', 'timestamp']
