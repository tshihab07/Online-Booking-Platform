from django.db import models
from django_mongodb_backend.fields import ObjectIdField

class Booking(models.Model):
    _id = ObjectIdField(primary_key=True)
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE)
    
    # Customer Info
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_notes = models.TextField(blank=True)
    customer_id = models.CharField(max_length=50, blank=True)  # For returning customers
    
    # Booking Details
    service = models.ForeignKey('businesses.Service', on_delete=models.CASCADE)
    staff = models.ForeignKey('businesses.Staff', on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    
    # Payment
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default='unpaid')
    payment_id = models.CharField(max_length=100, blank=True)
    
    # Metadata
    source = models.CharField(max_length=20, default='website')  # website, widget, manual
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bookings'
        indexes = [
            models.Index(fields=['business', 'date']),
            models.Index(fields=['business', 'customer_email']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate end_time based on service duration
        if self.start_time and self.service:
            from datetime import datetime, timedelta
            start_dt = datetime.combine(self.date, self.start_time)
            end_dt = start_dt + timedelta(minutes=self.service.duration)
            self.end_time = end_dt.time()
        super().save(*args, **kwargs)
