from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.db.models import Q
import datetime

from .models import ScheduleSlot, ChatMessage, Apartment, CustomUser

@login_required
def dashboard_view(request):
    """
    Main dashboard for users to view schedules and chat.
    """
    user_apartment_id = request.user.apartment_id
    if not user_apartment_id:
        # Handle users without an apartment_id (e.g., redirect to profile setup)
        return render(request, 'roomsync/no_apartment.html') # Create this template

    apartment = get_object_or_404(Apartment, apartment_id=user_apartment_id)

    # Get today's schedule
    today = timezone.localdate()
    start_of_day = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
    end_of_day = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))

    # Get schedules for the user's apartment for today
    apartment_schedules = ScheduleSlot.objects.filter(
        apartment=apartment,
        start_time__range=(start_of_day, end_of_day)
    ).order_by('start_time')

    # Get recent chat messages for the apartment
    chat_messages = ChatMessage.objects.filter(apartment=apartment).order_by('-timestamp')[:50] # Last 50 messages

    context = {
        'apartment_id': user_apartment_id,
        'schedules': apartment_schedules,
        'chat_messages': chat_messages,
        'current_user_email': request.user.email,
        'is_admin': request.user.apartment_id == 'admin', # Check for admin role
    }
    return render(request, 'roomsync/dashboard.html', context)

@login_required
def book_slot_api(request):
    """
    API endpoint to book a schedule slot. Handles conflict detection.
    """
    if request.method == 'POST':
        slot_type = request.POST.get('slot_type')
        start_time_str = request.POST.get('start_time') # Format: YYYY-MM-DDTHH:MM
        
        if not all([slot_type, start_time_str]):
            return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)

        try:
            start_time = timezone.make_aware(datetime.datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M'))
            
            # Calculate end time based on slot type
            if slot_type == 'bathroom':
                end_time = start_time + datetime.timedelta(minutes=15)
            elif slot_type == 'kitchen':
                end_time = start_time + datetime.timedelta(hours=1)
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid slot type'}, status=400)

            # Ensure booking is not in the past
            if start_time < timezone.now():
                return JsonResponse({'status': 'error', 'message': 'Cannot book a slot in the past.'}, status=400)

            user_apartment_id = request.user.apartment_id
            if not user_apartment_id:
                return JsonResponse({'status': 'error', 'message': 'User not assigned to an apartment.'}, status=400)

            apartment = get_object_or_404(Apartment, apartment_id=user_apartment_id)

            # Conflict Detection: Check for overlapping bookings in the same apartment
            # A new slot (start_time, end_time) conflicts if it overlaps with an existing slot (existing_start, existing_end)
            # Overlap conditions:
            # 1. New slot starts during existing slot: existing_start < start_time < existing_end
            # 2. New slot ends during existing slot: existing_start < end_time < existing_end
            # 3. Existing slot starts during new slot: start_time < existing_start < end_time
            # 4. Existing slot ends during new slot: start_time < existing_end < end_time
            # 5. New slot completely contains existing slot: start_time <= existing_start AND end_time >= existing_end
            # 6. Existing slot completely contains new slot: existing_start <= start_time AND existing_end >= end_time

            conflicting_slots = ScheduleSlot.objects.filter(
                apartment=apartment,
                start_time__lt=end_time, # Existing slot starts before new slot ends
                end_time__gt=start_time   # Existing slot ends after new slot starts
            ).exclude(user=request.user) # Optionally allow user to book multiple non-overlapping slots

            if conflicting_slots.exists():
                return JsonResponse({'status': 'error', 'message': 'This slot conflicts with an existing booking.'}, status=409) # 409 Conflict

            # Create the slot
            slot = ScheduleSlot.objects.create(
                user=request.user,
                apartment=apartment,
                slot_type=slot_type,
                start_time=start_time,
                end_time=end_time
            )
            return JsonResponse({'status': 'success', 'message': 'Slot booked successfully!'})

        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': f'Invalid date/time format: {e}'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def admin_dashboard_view(request):
    """
    Admin dashboard for housing staff to monitor all schedules.
    Requires the user to have apartment_id 'admin'.
    """
    if request.user.apartment_id != 'admin':
        return redirect('dashboard') # Redirect non-admin users

    # Get all apartments and their schedules
    all_apartments = Apartment.objects.all().order_by('apartment_id')
    all_schedules = ScheduleSlot.objects.all().order_by('start_time')

    # You might want to filter schedules by date or apartment for larger datasets
    context = {
        'all_apartments': all_apartments,
        'all_schedules': all_schedules,
    }
    return render(request, 'roomsync/admin_dashboard.html', context)