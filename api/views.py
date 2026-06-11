from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from datetime import datetime

from businesses.models import Business, Service, Staff
from bookings.models import Booking
from bookings.utils import get_available_slots, get_availability_heatmap, create_booking_atomic
from .serializers import (
    BusinessSerializer, ServiceSerializer, StaffSerializer,
    BookingSerializer, BookingCreateSerializer,
)
from .permissions import IsBusinessOwner
from platform_admin.plan_limits import check_api_access, record_api_call


def _api_plan_guard(business):
    """Return error Response if business plan lacks API access."""
    ok, msg = check_api_access(business)
    if not ok:
        return Response({'error': msg}, status=403)
    record_api_call(business)
    return None


# ─── Business ────────────────────────────────────────────────────────────────

class BusinessDetailAPI(generics.RetrieveAPIView):
    """GET /api/v1/businesses/<slug>/"""
    serializer_class = BusinessSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    queryset = Business.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        business = self.get_object()
        denied = _api_plan_guard(business)
        if denied:
            return denied
        return super().retrieve(request, *args, **kwargs)


class BusinessServicesAPI(generics.ListAPIView):
    """GET /api/v1/businesses/<slug>/services/"""
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        slug = self.kwargs['slug']
        business = get_object_or_404(Business, slug=slug, is_active=True)
        return Service.objects.filter(business=business, is_active=True)

    def list(self, request, *args, **kwargs):
        slug = self.kwargs['slug']
        business = get_object_or_404(Business, slug=slug, is_active=True)
        denied = _api_plan_guard(business)
        if denied:
            return denied
        return super().list(request, *args, **kwargs)


class BusinessStaffAPI(generics.ListAPIView):
    """GET /api/v1/businesses/<slug>/staff/"""
    serializer_class = StaffSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        slug = self.kwargs['slug']
        business = get_object_or_404(Business, slug=slug, is_active=True)
        return Staff.objects.filter(business=business, is_active=True)

    def list(self, request, *args, **kwargs):
        slug = self.kwargs['slug']
        business = get_object_or_404(Business, slug=slug, is_active=True)
        denied = _api_plan_guard(business)
        if denied:
            return denied
        return super().list(request, *args, **kwargs)


# ─── Availability ─────────────────────────────────────────────────────────────

class AvailabilityAPI(APIView):
    """GET /api/v1/businesses/<slug>/availability/"""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        business = get_object_or_404(Business, slug=slug, is_active=True)
        denied = _api_plan_guard(business)
        if denied:
            return denied
        service_id = request.query_params.get('service_id')
        staff_id = request.query_params.get('staff_id')
        date_str = request.query_params.get('date')

        if not service_id or not date_str:
            return Response({'error': 'service_id and date required'}, status=400)

        service = get_object_or_404(Service, pk=service_id, business=business, is_active=True)
        staff = None
        if staff_id:
            staff = Staff.objects.filter(pk=staff_id, business=business, is_active=True).first()

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        slots = get_available_slots(business, service, staff, target_date)
        return Response({'date': date_str, 'slots': slots})


class HeatmapAPI(APIView):
    """GET /api/v1/businesses/<slug>/heatmap/"""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        business = get_object_or_404(Business, slug=slug, is_active=True)
        denied = _api_plan_guard(business)
        if denied:
            return denied
        service_id = request.query_params.get('service_id')
        year = int(request.query_params.get('year', datetime.today().year))
        month = int(request.query_params.get('month', datetime.today().month))

        if not service_id:
            return Response({'error': 'service_id required'}, status=400)

        service = get_object_or_404(Service, pk=service_id, business=business, is_active=True)
        heatmap = get_availability_heatmap(business, service, year, month)
        return Response({'year': year, 'month': month, 'heatmap': heatmap})


# ─── Bookings ─────────────────────────────────────────────────────────────────

class BookingCreateAPI(APIView):
    """POST /api/v1/businesses/<slug>/bookings/"""
    permission_classes = [AllowAny]

    def post(self, request, slug):
        business = get_object_or_404(Business, slug=slug, is_active=True)
        denied = _api_plan_guard(business)
        if denied:
            return denied
        serializer = BookingCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        service = get_object_or_404(Service, pk=data['service_id'], business=business, is_active=True)
        staff = None
        if data.get('staff_id'):
            staff = Staff.objects.filter(pk=data['staff_id'], business=business, is_active=True).first()

        customer_data = {
            'customer_name': data['customer_name'],
            'customer_email': data['customer_email'],
            'customer_phone': data['customer_phone'],
            'customer_notes': data.get('customer_notes', ''),
        }

        booking, error = create_booking_atomic(
            business, service, staff, customer_data,
            data['date'], data['start_time'].strftime('%H:%M'),
        )

        if error:
            return Response({'error': error}, status=409)

        return Response(BookingSerializer(booking).data, status=201)


class BookingDetailAPI(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/bookings/<id>/"""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner]

    def get_queryset(self):
        user = self.request.user
        biz_ids = user.businesses or []
        return Booking.objects.filter(business__pk__in=biz_ids)

    def retrieve(self, request, *args, **kwargs):
        booking = self.get_object()
        denied = _api_plan_guard(booking.business)
        if denied:
            return denied
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        denied = _api_plan_guard(booking.business)
        if denied:
            return denied
        return super().update(request, *args, **kwargs)


class BookingListAPI(generics.ListAPIView):
    """GET /api/v1/businesses/<slug>/bookings/ (authenticated)"""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        slug = self.kwargs['slug']
        business = get_object_or_404(Business, slug=slug)
        denied = _api_plan_guard(business)
        if denied:
            return denied
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        slug = self.kwargs['slug']
        business = get_object_or_404(Business, slug=slug)
        user = self.request.user
        biz_ids = [str(b) for b in (user.businesses or [])]
        if str(business.pk) not in biz_ids and not user.is_superuser:
            return Booking.objects.none()

        qs = Booking.objects.filter(business=business).order_by('-date', '-start_time')

        # Filters
        date_str = self.request.query_params.get('date')
        status = self.request.query_params.get('status')
        if date_str:
            try:
                qs = qs.filter(date=datetime.strptime(date_str, '%Y-%m-%d').date())
            except ValueError:
                pass
        if status:
            qs = qs.filter(status=status)

        return qs
