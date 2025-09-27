# Register your models here.

from django.contrib import admin
from .models import WaterQuality, SymptomReport, Alert

admin.site.register(WaterQuality)
admin.site.register(SymptomReport)
admin.site.register(Alert)
