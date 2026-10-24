from django.urls import path
from .views import (
    RegisterAPIView, SubmitPaymentAPIView, PaymentStatusAPIView,
    LoginAPIView, LogoutAPIView, MeAPIView,
    MatchListAPIView, ProfileDetailAPIView, ProfileUpdateAPIView,
    InterestListSendAPIView, InterestRespondAPIView,
    ShortlistToggleAPIView, NotificationListAPIView,
    PublicPlansAPIView, PublicTestimonialsAPIView, PublicSuccessStoriesAPIView,
    PublicEnquiryAPIView, ReportProfileAPIView,
    AdminLoginAPIView, AdminStatsAPIView, AdminRegistrationPaymentsAPIView,
    AdminVerifyPaymentAPIView, AdminMemberActionAPIView, AdminAuditLogsAPIView
)

urlpatterns = [
    # Auth & Onboarding
    path('auth/register', RegisterAPIView.as_view(), name='api-register'),
    path('auth/submit-payment', SubmitPaymentAPIView.as_view(), name='api-submit-payment'),
    path('auth/payment-status', PaymentStatusAPIView.as_view(), name='api-payment-status'),
    path('auth/login', LoginAPIView.as_view(), name='api-login'),
    path('auth/logout', LogoutAPIView.as_view(), name='api-logout'),
    path('auth/me', MeAPIView.as_view(), name='api-me'),

    # Matches & Profiles
    path('matches', MatchListAPIView.as_view(), name='api-matches'),
    path('profile/<str:pk>', ProfileDetailAPIView.as_view(), name='api-profile-detail'),
    path('profile/edit', ProfileUpdateAPIView.as_view(), name='api-profile-edit'),

    # Member Interactions
    path('interests', InterestListSendAPIView.as_view(), name='api-interests'),
    path('interests/send', InterestListSendAPIView.as_view(), name='api-interest-send'),
    path('interests/respond', InterestRespondAPIView.as_view(), name='api-interest-respond'),
    path('shortlist', ShortlistToggleAPIView.as_view(), name='api-shortlist'),
    path('shortlist/toggle', ShortlistToggleAPIView.as_view(), name='api-shortlist-toggle'),
    path('notifications', NotificationListAPIView.as_view(), name='api-notifications'),
    path('notifications/read', NotificationListAPIView.as_view(), name='api-notifications-read'),

    # Public Data
    path('public/plans', PublicPlansAPIView.as_view(), name='api-public-plans'),
    path('public/testimonials', PublicTestimonialsAPIView.as_view(), name='api-public-testimonials'),
    path('public/success-stories', PublicSuccessStoriesAPIView.as_view(), name='api-public-success-stories'),
    path('public/enquiry', PublicEnquiryAPIView.as_view(), name='api-public-enquiry'),
    path('public/report-profile', ReportProfileAPIView.as_view(), name='api-public-report'),

    # Admin Management (Isolated for /sm-admin)
    path('admin/login', AdminLoginAPIView.as_view(), name='api-admin-login'),
    path('admin/stats', AdminStatsAPIView.as_view(), name='api-admin-stats'),
    path('admin/registration-payments', AdminRegistrationPaymentsAPIView.as_view(), name='api-admin-payments'),
    path('admin/verify-payment', AdminVerifyPaymentAPIView.as_view(), name='api-admin-verify-payment'),
    path('admin/member-action', AdminMemberActionAPIView.as_view(), name='api-admin-member-action'),
    path('admin/logs', AdminAuditLogsAPIView.as_view(), name='api-admin-logs'),
]
