# core/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# ----------------------------
# WATER QUALITY MODEL
# ----------------------------
class WaterQuality(models.Model):
    village = models.CharField(max_length=100)
    ph = models.FloatField()
    turbidity = models.FloatField()
    tds = models.FloatField()
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.village} - {self.timestamp}"


# ----------------------------
# SYMPTOM REPORT MODEL
# ----------------------------
class SymptomReport(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(
        max_length=10, 
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")]
    )
    contact = models.CharField(max_length=15, blank=True, null=True)

    village = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)

    symptoms = models.TextField()
    disease = models.CharField(max_length=100, blank=True, null=True)
    water_source = models.CharField(max_length=50, default="Other")
    image = models.ImageField(upload_to="reports/", blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    reported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.village} - {self.symptoms[:20]}"


# ----------------------------
# ALERT MODEL
# ----------------------------
class Alert(models.Model):
    ALERT_TYPES = (
        ("water", "Water Quality"),
        ("disease", "Predicted Disease"),
    )

    village = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default="water")
    message = models.TextField()
    status = models.CharField(max_length=20, default="unresolved")  # unresolved / resolved
    triggered_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"[{self.alert_type}] {self.village} - {self.status}"


# ----------------------------
# USER PROFILE MODEL (Optional)
# ----------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username
