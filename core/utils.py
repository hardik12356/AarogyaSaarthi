# core/utils.py

from django.utils import timezone
from .models import WaterQuality, SymptomReport, Alert

# ----------------------------
# SMS STUB FUNCTION
# ----------------------------
def send_sms_stub(to, body):
    """
    MVP placeholder for sending SMS.
    Prints the message to console. Replace with Twilio or actual SMS service later.
    """
    print(f"[SMS -> {to}] {body}")


# ----------------------------
# ALERT CHECKING FUNCTION
# ----------------------------
def check_and_trigger_alert():
    """
    Check all villages for unsafe water + symptom reports.
    Create alerts if thresholds are exceeded, avoiding duplicates.
    """
    # Get all villages that have water data or symptom reports
    villages = set(list(WaterQuality.objects.values_list("village", flat=True)) +
                   list(SymptomReport.objects.values_list("village", flat=True)))

    for v in villages:
        latest = WaterQuality.objects.filter(village=v).order_by('-timestamp').first()
        # Count symptom reports in last 2 days
        symptom_count = SymptomReport.objects.filter(
            village=v,
            reported_at__gte=timezone.now() - timezone.timedelta(days=2)
        ).count()

        # Determine if water is unsafe
        unsafe = False
        if latest:
            unsafe = (
                latest.ph < 6.5 or latest.ph > 8.5 or
                latest.turbidity > 5 or
                latest.tds > 500
            )

        # Trigger alert if unsafe and symptoms >= 3, avoiding duplicates
        if unsafe and symptom_count >= 3:
            if not Alert.objects.filter(village=v, resolved=False).exists():
                message = f"Potential outbreak risk in {v}. Unsafe water + {symptom_count} symptom reports."
                Alert.objects.create(village=v, message=message)
                send_sms_stub("ADMIN_NUMBER", message)


# ----------------------------
# WATER STATUS FUNCTION
# ----------------------------
def get_water_status(ph, turbidity, tds):
    """
    Determine water quality status based on WHO limits.
    Returns 'safe', 'warning', 'unsafe', or 'unknown'.
    """
    if ph is None or turbidity is None or tds is None:
        return "unknown"

    # Unsafe if any parameter is critically bad
    if ph < 6.5 or ph > 8.5 or turbidity > 10 or tds > 1000:
        return "unsafe"

    # Warning if turbidity or TDS slightly above safe limits
    if turbidity > 5 or tds > 500:
        return "warning"

    # Otherwise safe
    return "safe"


# ----------------------------
# DISEASE PREDICTION FUNCTION
# ----------------------------
def predict_disease(ph, turbidity, tds, symptom_reports=None):
    """
    Rule-based disease prediction based on water parameters and optional symptom reports.
    Returns a list of predicted diseases.
    """
    risks = []

    # Water quality based rules
    if ph is not None and (ph < 6.5 or ph > 8.5):
        risks.append("Gastroenteritis")
    if turbidity is not None and turbidity > 5:
        risks.append("Diarrhea")
    if tds is not None and tds > 500:
        risks.append("Typhoid")

    # Symptom-based rules
    if symptom_reports:
        if symptom_reports.get("diarrhea", 0) > 5:
            risks.append("Diarrhea")
        if symptom_reports.get("fever", 0) > 5:
            risks.append("Typhoid or Cholera")

    # Default to "None" if no risks found
    if not risks:
        risks.append("None")

    return risks
