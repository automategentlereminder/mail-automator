import datetime
import random
from core.database import get_setting

class Scheduler:
    @staticmethod
    def get_pulse_delay():
        """Returns a random delay in seconds based on pulse settings (The Humanizer)"""
        try:
            pulse_min = int(get_setting("pulse_min", "300"))
            pulse_max = int(get_setting("pulse_max", "600"))
            # Ensure safe bounds
            if pulse_min > pulse_max:
                pulse_min, pulse_max = pulse_max, pulse_min
            return random.randint(pulse_min, pulse_max)
        except:
            return 300 # Default fallback

    @staticmethod
    def can_send_now():
        """
        Checks if it's currently within allowed working hours and days.
        Returns: (bool, str) -> (is_allowed, reason)
        """
        now = datetime.datetime.now()
        
        # Check skip weekend
        skip_weekends = str(get_setting("skip_weekends", "1")).lower()
        if skip_weekends in ["1", "true", "yes"]:
            if now.weekday() >= 5: # 5 is Saturday, 6 is Sunday
                return False, "Skipping: Today is a weekend."
                
        # Check working hours
        try:
            start_str = get_setting("working_hours_start", "09:00")
            end_str = get_setting("working_hours_end", "18:00")
            
            start_time = datetime.datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.datetime.strptime(end_str, "%H:%M").time()
            
            current_time = now.time()
            
            if start_time < end_time:
                # Normal day interval (e.g., 09:00 to 18:00)
                if not (start_time <= current_time <= end_time):
                    return False, f"Outside working hours ({start_str} - {end_str})."
            else:
                # Spans midnight (e.g., 22:00 to 06:00)
                if not (current_time >= start_time or current_time <= end_time):
                    return False, f"Outside working hours ({start_str} - {end_str})."
        except Exception as e:
            # If settings are malformed, we just allow
            pass
            
        return True, "Allowed"

    @staticmethod
    def check_daily_limit(sent_today_count):
        """Checks if the daily limit has been reached."""
        try:
            limit = int(get_setting("daily_limit", "50"))
            if sent_today_count >= limit:
                return False, f"Daily limit of {limit} reached."
            return True, "Under limit"
        except:
            return True, "Limit error, allowing."
