import random
from django.contrib import admin
from django.utils import timezone
from .models import (
    RegistrationPayment, Profile, FamilyDetails, PartnerPreference,
    Interest, Shortlist, ContactRequest, Notification, MembershipPlan,
    UserMembership, Enquiry, ProfileReport, SuccessStory, Testimonial, ActivityAuditLog
)

@admin.action(description="Approve ₹2,000 GPay Payment & Activate Account")
def approve_gpay_payment(modeladmin, request, queryset):
    for payment in queryset:
        if payment.status != 'PAID':
            receipt_no = f"RCP-2026-{random.randint(1000, 9999)}"
            payment.status = 'PAID'
            payment.receipt_no = receipt_no
            payment.verified_at = timezone.now()
            payment.verified_by = request.user
            payment.admin_notes = "Approved via Django Admin interface."
            payment.save()

            user = payment.user
            user.is_active = True
            user.save()

            if hasattr(user, 'profile'):
                user.profile.is_approved = True
                user.profile.save()

            Notification.objects.create(
                user=user,
                title="Registration Verified & Profile Activated!",
                message=f"Your ₹2,000 GPay payment has been verified. Official Receipt: {receipt_no}. Welcome to Sarvamangala Matrimony!"
            )


@admin.register(RegistrationPayment)
class RegistrationPaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'transaction_ref', 'status', 'receipt_no', 'submitted_at', 'verified_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'transaction_ref', 'receipt_no']
    actions = [approve_gpay_payment]


class FamilyDetailsInline(admin.StackedInline):
    model = FamilyDetails
    can_delete = False


class PartnerPreferenceInline(admin.StackedInline):
    model = PartnerPreference
    can_delete = False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['profile_id', 'full_name', 'gender', 'age', 'caste', 'district', 'is_approved', 'is_active']
    list_filter = ['gender', 'caste', 'district', 'is_approved', 'is_active']
    search_fields = ['profile_id', 'full_name', 'phone', 'email', 'caste']
    inlines = [FamilyDetailsInline, PartnerPreferenceInline]


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'status', 'created_at']
    list_filter = ['status']


@admin.register(Shortlist)
class ShortlistAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'shortlisted_profile', 'created_at']


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ['requester', 'target', 'status', 'requested_at']
    list_filter = ['status']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read']


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_code', 'price', 'validity_days', 'contact_limit', 'is_active']


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'start_date', 'end_date', 'contacts_used', 'is_active']


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'subject', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['name', 'phone', 'email', 'subject']


@admin.register(ProfileReport)
class ProfileReportAdmin(admin.ModelAdmin):
    list_display = ['reported_profile', 'reporter', 'reason', 'status', 'created_at']
    list_filter = ['status']


@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display = ['couple_names', 'wedding_date', 'is_featured', 'created_at']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['reviewer_name', 'relation', 'city', 'rating', 'is_approved']
    list_filter = ['rating', 'is_approved']


@admin.register(ActivityAuditLog)
class ActivityAuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'actor', 'action', 'target_type', 'target_id']
    list_filter = ['action', 'target_type']
    search_fields = ['action', 'details', 'actor__username']
