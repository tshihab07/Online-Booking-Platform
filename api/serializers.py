from rest_framework import serializers
from businesses.models import Business, Service, Staff
from bookings.models import Booking


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'duration', 'price', 'category', 'image', 'max_capacity', 'color', 'is_active')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = str(instance.pk)
        return data


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('id', 'name', 'email', 'phone', 'bio', 'avatar', 'availability', 'services', 'is_active')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = str(instance.pk)
        return data


class BusinessSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    staff_members = StaffSerializer(many=True, read_only=True)

    class Meta:
        model = Business
        fields = (
            'id', 'name', 'slug', 'description', 'business_type',
            'email', 'phone', 'address', 'website',
            'theme', 'brand_colors', 'working_hours',
            'timezone', 'currency', 'booking_lead_time',
            'max_booking_per_slot', 'buffer_time',
            'plan', 'is_active',
            'services', 'staff_members',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = str(instance.pk)
        return data


class BookingSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    staff_name = serializers.CharField(source='staff.name', read_only=True, allow_null=True)

    class Meta:
        model = Booking
        fields = (
            'id', 'business', 'service', 'service_name', 'staff', 'staff_name',
            'customer_name', 'customer_email', 'customer_phone', 'customer_notes',
            'date', 'start_time', 'end_time',
            'status', 'amount', 'payment_status', 'payment_id',
            'source', 'reminder_sent', 'created_at',
        )
        read_only_fields = ('end_time', 'created_at', 'amount')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = str(instance.pk)
        data['business'] = str(instance.business_id)
        data['service'] = str(instance.service_id)
        if instance.staff_id:
            data['staff'] = str(instance.staff_id)
        return data


class BookingCreateSerializer(serializers.Serializer):
    service_id = serializers.CharField()
    staff_id = serializers.CharField(required=False, allow_blank=True)
    date = serializers.DateField()
    start_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=20)
    customer_notes = serializers.CharField(required=False, allow_blank=True)
