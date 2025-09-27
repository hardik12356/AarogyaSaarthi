# core/views.py

import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .forms import SymptomReportForm, RegisterForm, LoginForm
from .models import WaterQuality, SymptomReport, Alert
from .utils import predict_disease, check_and_trigger_alert

# Fallback coordinates for villages if GPS data is missing
FALLBACK_COORDS = {
    "Village A": (26.0, 92.0),
    "Village B": (26.1, 92.2),
    "Village C": (26.2, 92.4),
}


# ----------------------------
# DASHBOARD
# ----------------------------
# @login_required
def dashboard(request):
    """
    Display dashboard with recent water quality data, symptom reports, alerts,
    village summary, and charts.
    """
    # Fetch recent water quality and symptom reports
    water_data = WaterQuality.objects.all().order_by('-timestamp')[:20]
    recent_reports = SymptomReport.objects.all().order_by('-reported_at')[:10]
    alerts = Alert.objects.filter(status="active").order_by('-triggered_at')

    # Build village summary data
    villages = []
    villages_set = set(list(WaterQuality.objects.values_list("village", flat=True)) +
                       list(SymptomReport.objects.values_list("village", flat=True)))

    for v in villages_set:
        latest_water = WaterQuality.objects.filter(village=v).order_by('-timestamp').first()
        symptom_count = SymptomReport.objects.filter(
            village=v,
            reported_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()

        # Use fallback coordinates if missing
        if latest_water:
            lat = latest_water.lat if latest_water.lat is not None else FALLBACK_COORDS.get(v, (26.2, 92.9))[0]
            lng = latest_water.lng if latest_water.lng is not None else FALLBACK_COORDS.get(v, (26.2, 92.9))[1]
            ph = latest_water.ph
            turbidity = latest_water.turbidity
            tds = latest_water.tds
        else:
            lat, lng = FALLBACK_COORDS.get(v, (26.2, 92.9))
            ph = turbidity = tds = None

        # Determine water status
        status = "safe"
        if (ph and (ph < 6.5 or ph > 8.5)) or (turbidity and turbidity > 5) or (tds and tds > 500):
            status = "warning"
        if (ph and (ph < 6.0 or ph > 9.0)) or (turbidity and turbidity > 8) or (tds and tds > 700):
            status = "unsafe"

        # Predicted diseases based on water quality and symptom reports
        symptom_reports = {
            "diarrhea": SymptomReport.objects.filter(village=v, symptoms__icontains="diarrhea").count(),
            "fever": SymptomReport.objects.filter(village=v, symptoms__icontains="fever").count()
        }
        diseases = predict_disease(ph, turbidity, tds, symptom_reports)

        villages.append({
            "village": v,
            "lat": lat,
            "lng": lng,
            "ph": ph,
            "turbidity": turbidity,
            "tds": tds,
            "symptom_count": symptom_count,
            "status": status,
            "predicted_disease": diseases
        })

    # Chart: 7-day symptom counts
    days, counts = [], []
    for i in range(6, -1, -1):
        day = (timezone.now() - timezone.timedelta(days=i)).date()
        days.append(day.strftime("%b %d"))
        counts.append(SymptomReport.objects.filter(reported_at__date=day).count())

    context = {
        "water_data": water_data,
        "recent_reports": recent_reports,
        "alerts": alerts,
        "villages_json": json.dumps(villages),
        "chart_json": json.dumps({"labels": days, "data": counts})
    }
    return render(request, "core/dashboard.html", context)


# ----------------------------
# SYMPTOM REPORT FORM
# ----------------------------
def report_symptoms(request):
    """
    Handle symptom reporting by users via form submission.
    """
    if request.method == "POST":
        form = SymptomReportForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Your report has been submitted successfully.")
            return redirect("report_symptoms")
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = SymptomReportForm()
    return render(request, "core/report_symptom.html", {"form": form})


# ----------------------------
# WATER QUALITY API (POST)
# ----------------------------
@csrf_exempt
def water_api(request):
    """
    Receive water quality data from sensors or simulator.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    try:
        data = json.loads(request.body)
        WaterQuality.objects.create(
            village=data.get("village"),
            ph=float(data.get("ph")),
            turbidity=float(data.get("turbidity")),
            tds=float(data.get("tds")),
            lat=float(data.get("lat")) if data.get("lat") else None,
            lng=float(data.get("lng")) if data.get("lng") else None
        )
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ----------------------------
# GET LATEST WATER DATA
# ----------------------------
def api_water(request):
    """
    Return latest water reading for frontend display.
    """
    latest = WaterQuality.objects.order_by("-timestamp").first()
    if not latest:
        return JsonResponse({"error": "No data yet"}, status=404)

    return JsonResponse({
        "village": latest.village,
        "ph": latest.ph,
        "turbidity": latest.turbidity,
        "tds": latest.tds,
        "lat": latest.lat,
        "lng": latest.lng,
        "timestamp": latest.timestamp,
    })


# ----------------------------
# VILLAGE SUMMARY API
# ----------------------------
def api_summary(request):
    """
    Provide summarized village data, water quality, predicted diseases, and trigger alerts.
    """
    villages = []
    villages_set = set(list(WaterQuality.objects.values_list("village", flat=True)) +
                       list(SymptomReport.objects.values_list("village", flat=True)))

    for v in villages_set:
        latest = WaterQuality.objects.filter(village=v).order_by('-timestamp').first()
        sym_count = SymptomReport.objects.filter(village=v).count()

        if latest:
            lat = latest.lat if latest.lat else 26.2
            lng = latest.lng if latest.lng else 92.9
            ph = latest.ph
            turbidity = latest.turbidity
            tds = latest.tds
        else:
            lat, lng = 26.2, 92.9
            ph = turbidity = tds = None

        # Decide status based on thresholds
        status = "safe"
        if (ph and (ph < 6.5 or ph > 8.5)) or (turbidity and turbidity > 5) or (tds and tds > 500):
            status = "warning"
        if (ph and (ph < 6.0 or ph > 9.0)) or (turbidity and turbidity > 8) or (tds and tds > 700):
            status = "unsafe"

        # Predicted diseases
        symptom_reports = {
            "diarrhea": SymptomReport.objects.filter(village=v, symptoms__icontains="diarrhea").count(),
            "fever": SymptomReport.objects.filter(village=v, symptoms__icontains="fever").count()
        }
        diseases = predict_disease(ph, turbidity, tds, symptom_reports)

        # Generate alerts if necessary
        if status in ["warning", "unsafe"]:
            exists = Alert.objects.filter(village=v, alert_type="water", status="unresolved").exists()
            if not exists:
                Alert.objects.create(
                    village=v,
                    alert_type="water",
                    message=f"Water quality {status.upper()} in {v}. pH={ph}, Turbidity={turbidity}, TDS={tds}",
                    status="unresolved",
                    triggered_at=timezone.now()
                )

        if diseases and diseases != ["None"]:
            exists = Alert.objects.filter(village=v, alert_type="disease", status="unresolved").exists()
            if not exists:
                Alert.objects.create(
                    village=v,
                    alert_type="disease",
                    message=f"Predicted disease risk in {v}: {', '.join(diseases)}",
                    status="unresolved",
                    triggered_at=timezone.now()
                )

        villages.append({
            "village": v,
            "lat": lat,
            "lng": lng,
            "ph": ph,
            "turbidity": turbidity,
            "tds": tds,
            "symptom_count": sym_count,
            "predicted_disease": diseases,
            "status": status
        })

    return JsonResponse({"villages": villages})


# ----------------------------
# EDUCATIONAL MODULES
# ----------------------------
def educational_modules(request):
    """
    Render educational modules page.
    """
    return render(request, "core/educational_modules.html")


# ----------------------------
# USER AUTHENTICATION
# ----------------------------
def register_view(request):
    """
    User registration page.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    """
    User login page.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome {user.username}!")
            return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """
    Logout user.
    """
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')


# ----------------------------
# DUMMY REPORT (For Testing)
# ----------------------------
def add_dummy_report(request):
    """
    Add a dummy symptom report for testing purposes.
    """
    SymptomReport.objects.create(
        name="Test User",
        village="DemoVillage",
        gender="Male",
        age=25,
        contact="9876543210",
        state="Assam",
        district="DemoDistrict",
        disease="Diarrhea",
        symptoms="Fever, Dehydration",
        remarks="Dummy entry from dashboard",
        reported_at=timezone.now()
    )
    return redirect("dashboard")


# ----------------------------
# ALERTS API
# ----------------------------
def alerts_api(request):
    """
    Fetch last 20 active alerts for frontend.
    """
    alerts = Alert.objects.filter(status="active").order_by('-triggered_at')[:20]
    data = [
        {
            "village": a.village,
            "alert_type": a.alert_type,
            "message": a.message,
            "status": a.status,
            "triggered_at": a.triggered_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for a in alerts
    ]
    return JsonResponse({"alerts": data})


# ----------------------------
# STATIC PAGES
# ----------------------------
def home(request):
    return render(request, 'core/home.html')

def help(request):
    return render(request, 'core/help.html')

def contact(request):
    return render(request, 'core/contact.html')
