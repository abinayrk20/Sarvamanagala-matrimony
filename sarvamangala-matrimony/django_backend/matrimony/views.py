import random
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from .models import (
    RegistrationPayment, Profile, FamilyDetails, PartnerPreference,
    Interest, Shortlist, ContactRequest, Notification, MembershipPlan,
    UserMembership, Enquiry, ProfileReport, SuccessStory, Testimonial, ActivityAuditLog
)
from .serializers import (
    RegistrationSerializer, RegistrationPaymentSerializer, ProfileListSerializer,
    ProfileDetailSerializer, InterestSerializer, ShortlistSerializer,
    ContactRequestSerializer, NotificationSerializer, MembershipPlanSerializer,
    EnquirySerializer, ProfileReportSerializer, SuccessStorySerializer,
    TestimonialSerializer, ActivityAuditLogSerializer, UserSerializer
)
from .permissions import IsAdminOrStaff, IsActiveAndPaidMember

# ==============================================================================
# AUTHENTICATION & REGISTRATION ENDPOINTS
# ==============================================================================

class RegisterAPIView(APIView):
    """
    POST /api/auth/register
    Creates a new candidate account.
    Status starts as PENDING until the mandatory ₹2,000 GPay payment is verified by Admin.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            profile = result['profile']
            payment = result['payment']

            # Create welcome notification
            Notification.objects.create(
                user=result['user'],
                title="Registration Received - Payment Pending",
                message=f"Welcome {profile.full_name}! Please complete the ₹2,000 registration fee via Google Pay to 9942006877 (UPI: 9942006877@upi) and submit your 12-digit UTR to activate your profile."
            )

            # Log audit
            ActivityAuditLog.objects.create(
                actor=None,
                action="REGISTER_SUBMITTED",
                target_type="User",
                target_id=str(result['user'].id),
                details=f"New candidate registered: {profile.full_name} ({profile.profile_id}), Phone: {profile.phone}"
            )

            return Response({
                "success": True,
                "message": "Registration successful! Complete the ₹2,000 GPay fee to activate your profile.",
                "profile_id": profile.profile_id,
                "user_id": result['user'].id,
                "payment": {
                    "amount": 2000,
                    "currency": "INR",
                    "payee_name": "Sarvamangala Matrimony Kanchipuram",
                    "payee_mobile": "9942006877",
                    "upi_id": "9942006877@upi",
                    "status": payment.status
                }
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SubmitPaymentAPIView(APIView):
    """
    POST /api/auth/submit-payment
    Candidate submits their 12-digit UPI / UTR Transaction ID.
    Transitions status: PENDING -> PAYMENT_SUBMITTED.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email_or_phone = request.data.get('email_or_phone', '').strip()
        transaction_ref = request.data.get('transaction_ref', '').strip()

        if not transaction_ref or len(transaction_ref) < 8:
            return Response({
                "success": False,
                "error": "Please enter a valid 12-digit UPI / UTR Transaction reference number."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Locate user either by logged-in session or email/phone
        user = None
        if request.user.is_authenticated:
            user = request.user
        elif email_or_phone:
            user = User.objects.filter(
                Q(email__iexact=email_or_phone) | Q(profile__phone=email_or_phone)
            ).first()

        if not user or not hasattr(user, 'registration_payment'):
            return Response({
                "success": False,
                "error": "Registration record not found. Please register first or provide your registered email/mobile."
            }, status=status.HTTP_404_NOT_FOUND)

        reg_payment = user.registration_payment
        reg_payment.transaction_ref = transaction_ref
        reg_payment.status = 'PAYMENT_SUBMITTED'
        reg_payment.submitted_at = timezone.now()
        reg_payment.save()

        # Create notification
        Notification.objects.create(
            user=user,
            title="Payment Submitted",
            message=f"UTR {transaction_ref} submitted for ₹2,000 registration fee. Admin verification is in progress."
        )

        # Audit log
        ActivityAuditLog.objects.create(
            actor=user,
            action="PAYMENT_SUBMITTED",
            target_type="RegistrationPayment",
            target_id=str(reg_payment.id),
            details=f"UTR {transaction_ref} submitted by {user.username} for ₹2,000 fee."
        )

        return Response({
            "success": True,
            "message": "Payment reference submitted successfully! Our Kanchipuram admin team will verify and activate your account.",
            "status": "PAYMENT_SUBMITTED",
            "transaction_ref": transaction_ref
        })


class PaymentStatusAPIView(APIView):
    """
    GET /api/auth/payment-status?ref=<email_or_phone>
    Polls the current status of the ₹2,000 registration payment.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        ref = request.query_params.get('ref', '').strip()
        user = None
        if request.user.is_authenticated:
            user = request.user
        elif ref:
            user = User.objects.filter(
                Q(email__iexact=ref) | Q(profile__phone=ref) | Q(profile__profile_id__iexact=ref)
            ).first()

        if not user or not hasattr(user, 'registration_payment'):
            return Response({"status": "NOT_FOUND"}, status=status.HTTP_404_NOT_FOUND)

        payment = user.registration_payment
        return Response({
            "status": payment.status,
            "amount": float(payment.amount),
            "transaction_ref": payment.transaction_ref,
            "receipt_no": payment.receipt_no,
            "is_active": user.is_active,
            "verified_at": payment.verified_at
        })


class LoginAPIView(APIView):
    """
    POST /api/auth/login
    Authenticates user. Verifies that account is activated and ₹2,000 payment has been verified.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username_or_email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        # Lookup user by username or email
        user_obj = User.objects.filter(
            Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)
        ).first()

        if not user_obj:
            return Response({"success": False, "error": "Invalid email/username or password."}, status=status.HTTP_401_UNAUTHORIZED)

        user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            return Response({"success": False, "error": "Invalid email/username or password."}, status=status.HTTP_401_UNAUTHORIZED)

        # Check payment / activation status (skip check for staff)
        if not user.is_staff:
            if hasattr(user, 'registration_payment'):
                payment = user.registration_payment
                if payment.status in ('PENDING', 'PAYMENT_SUBMITTED'):
                    return Response({
                        "success": False,
                        "payment_pending": True,
                        "status": payment.status,
                        "error": "Your registration payment of ₹2,000 is awaiting admin verification. Once verified, your account will activate.",
                        "upi_id": payment.upi_id,
                        "payee_mobile": payment.payee_mobile,
                        "transaction_ref": payment.transaction_ref
                    }, status=status.HTTP_403_FORBIDDEN)
                elif payment.status == 'REJECTED':
                    return Response({
                        "success": False,
                        "error": "Payment verification failed. Please contact our helpline at 8248853928 or resubmit your UTR."
                    }, status=status.HTTP_403_FORBIDDEN)

            if not user.is_active:
                return Response({"success": False, "error": "Your account is pending activation by admin."}, status=status.HTTP_403_FORBIDDEN)

        login(request, user)

        # Audit log
        ActivityAuditLog.objects.create(
            actor=user,
            action="LOGIN_SUCCESS",
            target_type="User",
            target_id=str(user.id),
            details=f"User {user.username} logged in successfully."
        )

        profile_data = None
        if hasattr(user, 'profile'):
            profile_data = ProfileDetailSerializer(user.profile).data

        return Response({
            "success": True,
            "message": "Login successful!",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff
            },
            "profile": profile_data
        })


class LogoutAPIView(APIView):
    """
    POST /api/auth/logout
    """
    def post(self, request):
        if request.user.is_authenticated:
            ActivityAuditLog.objects.create(
                actor=request.user,
                action="LOGOUT",
                target_type="User",
                target_id=str(request.user.id),
                details=f"User {request.user.username} logged out."
            )
            logout(request)
        return Response({"success": True, "message": "Logged out successfully."})


class MeAPIView(APIView):
    """
    GET /api/auth/me
    Returns active user profile, pending notifications count, and membership info.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile_data = None
        if hasattr(user, 'profile'):
            profile_data = ProfileDetailSerializer(user.profile).data

        unread_notifications = Notification.objects.filter(user=user, is_read=False).count()

        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_active": user.is_active
            },
            "profile": profile_data,
            "unread_notifications": unread_notifications
        })


# ==============================================================================
# MATCHES & DIRECTORY ENDPOINTS
# ==============================================================================

class MatchListAPIView(APIView):
    """
    GET /api/matches
    Search, filter, and paginate matrimonial profiles.
    Only approved, active, and visible profiles are shown.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Profile.objects.filter(is_active=True, is_approved=True, is_visible=True)

        # Filters
        gender = request.query_params.get('gender')
        if gender in ('M', 'F'):
            queryset = queryset.filter(gender=gender)

        age_min = request.query_params.get('age_min')
        if age_min and age_min.isdigit():
            queryset = queryset.filter(age__gte=int(age_min))

        age_max = request.query_params.get('age_max')
        if age_max and age_max.isdigit():
            queryset = queryset.filter(age__lte=int(age_max))

        caste = request.query_params.get('caste')
        if caste and caste != 'All' and caste != 'all':
            queryset = queryset.filter(caste__icontains=caste)

        district = request.query_params.get('district')
        if district and district != 'All' and district != 'all':
            queryset = queryset.filter(district__icontains=district)

        keyword = request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(
                Q(full_name__icontains=keyword) |
                Q(education__icontains=keyword) |
                Q(occupation__icontains=keyword) |
                Q(city__icontains=keyword) |
                Q(profile_id__icontains=keyword)
            )

        # Pagination
        page_num = int(request.query_params.get('page', 1))
        page_size = 12
        total_count = queryset.count()
        start = (page_num - 1) * page_size
        end = start + page_size

        profiles = queryset[start:end]
        serializer = ProfileListSerializer(profiles, many=True)

        return Response({
            "total": total_count,
            "page": page_num,
            "page_size": page_size,
            "profiles": serializer.data
        })


class ProfileDetailAPIView(APIView):
    """
    GET /api/profile/<id>
    Returns detailed profile view. Contact phone is only revealed if authorized.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        profile = Profile.objects.filter(Q(id=pk) | Q(profile_id__iexact=pk)).first()
        if not profile:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileDetailSerializer(profile)
        data = serializer.data

        # Privacy rules for phone & contact
        can_view_contact = False
        if request.user.is_authenticated:
            if request.user.is_staff or request.user == profile.user:
                can_view_contact = True
            elif hasattr(request.user, 'profile'):
                # Check if contact request was approved
                if ContactRequest.objects.filter(
                    requester=request.user.profile, target=profile, status='APPROVED'
                ).exists():
                    can_view_contact = True

        if not can_view_contact:
            # Obfuscate phone number for privacy
            raw_phone = data.get('phone', '')
            data['phone'] = raw_phone[:3] + '*****' + raw_phone[-2:] if len(raw_phone) >= 10 else 'Protected'
            data['email'] = 'Protected'

        return Response(data)


class ProfileUpdateAPIView(APIView):
    """
    POST /api/profile/edit
    Allows authenticated candidate to edit personal, horoscope, and family details.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, 'profile'):
            return Response({"error": "Profile does not exist."}, status=status.HTTP_404_NOT_FOUND)

        profile = request.user.profile
        data = request.data

        # Update allowed fields
        for field in ['full_name', 'caste', 'sub_caste', 'gothram', 'star_nakshatram', 'rasi', 'dosham', 'education', 'occupation', 'annual_income', 'city', 'district', 'about_me']:
            if field in data:
                setattr(profile, field, data[field])
        profile.save()

        # Update family if provided
        if hasattr(profile, 'family'):
            family = profile.family
            for f_field in ['father_name', 'father_occupation', 'mother_name', 'mother_occupation', 'family_status', 'native_place']:
                if f_field in data:
                    setattr(family, f_field, data[f_field])
            family.save()

        return Response({"success": True, "message": "Profile updated successfully!"})


# ==============================================================================
# INTERACTIONS (INTERESTS, SHORTLIST, CONTACT REQUESTS)
# ==============================================================================

class InterestListSendAPIView(APIView):
    """
    GET /api/interests - View sent and received interests
    POST /api/interests/send - Send express interest to a candidate
    """
    permission_classes = [IsActiveAndPaidMember]

    def get(self, request):
        my_profile = request.user.profile
        sent = Interest.objects.filter(sender=my_profile)
        received = Interest.objects.filter(receiver=my_profile)
        return Response({
            "sent": InterestSerializer(sent, many=True).data,
            "received": InterestSerializer(received, many=True).data
        })

    def post(self, request):
        my_profile = request.user.profile
        target_id = request.data.get('target_profile_id')
        target = Profile.objects.filter(Q(id=target_id) | Q(profile_id__iexact=target_id)).first()

        if not target:
            return Response({"error": "Target profile not found."}, status=status.HTTP_404_NOT_FOUND)
        if target == my_profile:
            return Response({"error": "You cannot express interest in your own profile."}, status=status.HTTP_400_BAD_REQUEST)

        interest, created = Interest.objects.get_or_create(
            sender=my_profile,
            receiver=target,
            defaults={'status': 'PENDING', 'message': request.data.get('message', 'Expressed interest in your profile.')}
        )

        if not created and interest.status == 'WITHDRAWN':
            interest.status = 'PENDING'
            interest.save()

        # Send notification to receiver
        Notification.objects.create(
            user=target.user,
            title="New Interest Received!",
            message=f"{my_profile.full_name} ({my_profile.profile_id}) has expressed interest in your profile."
        )

        return Response({"success": True, "message": "Interest sent successfully!"})


class InterestRespondAPIView(APIView):
    """
    POST /api/interests/respond
    Accept or Decline received interest.
    """
    permission_classes = [IsActiveAndPaidMember]

    def post(self, request):
        interest_id = request.data.get('interest_id')
        action = request.data.get('action') # 'accept' or 'decline'
        interest = Interest.objects.filter(id=interest_id, receiver=request.user.profile).first()

        if not interest:
            return Response({"error": "Interest request not found."}, status=status.HTTP_404_NOT_FOUND)

        if action == 'accept':
            interest.status = 'ACCEPTED'
            Notification.objects.create(
                user=interest.sender.user,
                title="Interest Accepted!",
                message=f"{request.user.profile.full_name} accepted your interest request!"
            )
        elif action == 'decline':
            interest.status = 'DECLINED'
        else:
            return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        interest.save()
        return Response({"success": True, "status": interest.status})


class ShortlistToggleAPIView(APIView):
    """
    GET /api/shortlist - Get bookmarked profiles
    POST /api/shortlist/toggle - Add or remove profile from bookmarks
    """
    permission_classes = [IsActiveAndPaidMember]

    def get(self, request):
        shortlists = Shortlist.objects.filter(user_profile=request.user.profile)
        return Response(ShortlistSerializer(shortlists, many=True).data)

    def post(self, request):
        target_id = request.data.get('target_profile_id')
        target = Profile.objects.filter(Q(id=target_id) | Q(profile_id__iexact=target_id)).first()
        if not target:
            return Response({"error": "Target profile not found."}, status=status.HTTP_404_NOT_FOUND)

        my_profile = request.user.profile
        existing = Shortlist.objects.filter(user_profile=my_profile, shortlisted_profile=target).first()

        if existing:
            existing.delete()
            return Response({"shortlisted": False, "message": "Removed from shortlist."})
        else:
            Shortlist.objects.create(user_profile=my_profile, shortlisted_profile=target)
            return Response({"shortlisted": True, "message": "Added to shortlist."})


class NotificationListAPIView(APIView):
    """
    GET /api/notifications - List user's notifications
    POST /api/notifications/read - Mark all as read
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notes = Notification.objects.filter(user=request.user)
        return Response(NotificationSerializer(notes, many=True).data)

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"success": True, "message": "All notifications marked as read."})


# ==============================================================================
# PUBLIC INFORMATION ENDPOINTS
# ==============================================================================

class PublicPlansAPIView(APIView):
    """
    GET /api/public/plans
    Returns available membership tiers.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        plans = MembershipPlan.objects.filter(is_active=True).order_by('price')
        serializer = MembershipPlanSerializer(plans, many=True)
        return Response({"plans": serializer.data})


class PublicTestimonialsAPIView(APIView):
    """
    GET /api/public/testimonials
    """
    permission_classes = [AllowAny]

    def get(self, request):
        items = Testimonial.objects.filter(is_approved=True)
        return Response({"testimonials": TestimonialSerializer(items, many=True).data})


class PublicSuccessStoriesAPIView(APIView):
    """
    GET /api/public/success-stories
    """
    permission_classes = [AllowAny]

    def get(self, request):
        stories = SuccessStory.objects.filter(is_featured=True)
        return Response({"stories": SuccessStorySerializer(stories, many=True).data})


class PublicEnquiryAPIView(APIView):
    """
    POST /api/public/enquiry
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EnquirySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Thank you! Our Kanchipuram office will contact you shortly."})
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ReportProfileAPIView(APIView):
    """
    POST /api/public/report-profile
    """
    permission_classes = [AllowAny]

    def post(self, request):
        reported_id = request.data.get('profile_id')
        reason = request.data.get('reason', '')
        details = request.data.get('details', '')

        target = Profile.objects.filter(Q(id=reported_id) | Q(profile_id__iexact=reported_id)).first()
        if not target:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        reporter = request.user if request.user.is_authenticated else None
        ProfileReport.objects.create(
            reporter=reporter,
            reported_profile=target,
            reason=reason,
            details=details
        )
        return Response({"success": True, "message": "Report logged. Admin will review within 24 hours."})


# ==============================================================================
# ADMIN PORTAL ENDPOINTS (ISOLATED AT /sm-admin)
# ==============================================================================

class AdminLoginAPIView(APIView):
    """
    POST /api/admin/login
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if not user or not user.is_staff:
            return Response({"success": False, "error": "Invalid administrative credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        ActivityAuditLog.objects.create(
            actor=user,
            action="ADMIN_LOGIN",
            target_type="Admin",
            target_id=str(user.id),
            details="Admin logged in to management dashboard."
        )
        return Response({"success": True, "message": "Admin authenticated."})


class AdminStatsAPIView(APIView):
    """
    GET /api/admin/stats
    """
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        total_profiles = Profile.objects.count()
        approved_profiles = Profile.objects.filter(is_approved=True).count()
        pending_payments = RegistrationPayment.objects.filter(status='PAYMENT_SUBMITTED').count()
        total_revenue = RegistrationPayment.objects.filter(status='PAID').count() * 2000
        open_enquiries = Enquiry.objects.filter(is_resolved=False).count()

        return Response({
            "total_profiles": total_profiles,
            "approved_profiles": approved_profiles,
            "pending_payments": pending_payments,
            "total_revenue": total_revenue,
            "open_enquiries": open_enquiries
        })


class AdminRegistrationPaymentsAPIView(APIView):
    """
    GET /api/admin/registration-payments
    Returns the queue of ₹2,000 GPay registration payments awaiting verification.
    """
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        status_filter = request.query_params.get('status')
        queryset = RegistrationPayment.objects.all().select_related('user', 'user__profile')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        serializer = RegistrationPaymentSerializer(queryset, many=True)
        return Response({"payments": serializer.data})


class AdminVerifyPaymentAPIView(APIView):
    """
    POST /api/admin/verify-payment
    Admin verifies the ₹2,000 GPay payment against bank/UPI records:
    - Status set to PAID
    - Account activated (user.is_active = True)
    - Profile approved (profile.is_approved = True)
    - Generates official receipt number: RCP-2026-XXXX
    """
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        payment_id = request.data.get('payment_id')
        decision = request.data.get('decision', 'approve') # 'approve' or 'reject'
        admin_notes = request.data.get('notes', '')

        payment = RegistrationPayment.objects.filter(id=payment_id).first()
        if not payment:
            return Response({"error": "Payment record not found."}, status=status.HTTP_404_NOT_FOUND)

        user = payment.user
        if decision == 'approve':
            receipt_no = f"RCP-2026-{random.randint(1000, 9999)}"
            payment.status = 'PAID'
            payment.receipt_no = receipt_no
            payment.verified_at = timezone.now()
            payment.verified_by = request.user
            payment.admin_notes = admin_notes or "Verified against GPay 9942006877 statement."
            payment.save()

            # Activate User & Approve Profile
            user.is_active = True
            user.save()

            if hasattr(user, 'profile'):
                user.profile.is_approved = True
                user.profile.save()

            # Notification to candidate
            Notification.objects.create(
                user=user,
                title="Registration Verified & Profile Activated!",
                message=f"Your ₹2,000 GPay payment (UTR: {payment.transaction_ref}) is verified. Official Receipt: {receipt_no}. You may now log in and connect with families!"
            )

            # Audit log
            ActivityAuditLog.objects.create(
                actor=request.user,
                action="APPROVE_GPAY_PAYMENT",
                target_type="RegistrationPayment",
                target_id=str(payment.id),
                details=f"Approved ₹2,000 fee for {user.username}. Receipt: {receipt_no}."
            )

            return Response({
                "success": True,
                "message": f"Payment verified! Account activated. Receipt {receipt_no} generated.",
                "receipt_no": receipt_no
            })

        elif decision == 'reject':
            payment.status = 'REJECTED'
            payment.admin_notes = admin_notes or "UTR verification failed with bank statement."
            payment.save()

            Notification.objects.create(
                user=user,
                title="Payment Verification Failed",
                message="Your submitted UTR could not be verified. Please check and resubmit or contact 8248853928."
            )

            ActivityAuditLog.objects.create(
                actor=request.user,
                action="REJECT_GPAY_PAYMENT",
                target_type="RegistrationPayment",
                target_id=str(payment.id),
                details=f"Rejected payment for {user.username}. Notes: {admin_notes}."
            )

            return Response({"success": True, "message": "Payment rejected."})

        return Response({"error": "Invalid decision."}, status=status.HTTP_400_BAD_REQUEST)


class AdminMemberActionAPIView(APIView):
    """
    POST /api/admin/member-action
    Admin can toggle approval, suspend, or delete a profile.
    """
    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        profile_id = request.data.get('profile_id')
        action = request.data.get('action') # 'approve', 'suspend', 'delete'

        profile = Profile.objects.filter(Q(id=profile_id) | Q(profile_id__iexact=profile_id)).first()
        if not profile:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        if action == 'approve':
            profile.is_approved = True
            profile.is_active = True
            profile.save()
        elif action == 'suspend':
            profile.is_active = False
            profile.save()
        elif action == 'delete':
            profile.user.delete()
            return Response({"success": True, "message": "Profile and user account deleted."})

        ActivityAuditLog.objects.create(
            actor=request.user,
            action=f"MEMBER_{action.upper()}",
            target_type="Profile",
            target_id=str(profile.id),
            details=f"Admin performed {action} on {profile.profile_id}."
        )

        return Response({"success": True, "message": f"Action '{action}' completed."})


class AdminAuditLogsAPIView(APIView):
    """
    GET /api/admin/logs
    """
    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        logs = ActivityAuditLog.objects.all()[:100]
        return Response({"logs": ActivityAuditLogSerializer(logs, many=True).data})
