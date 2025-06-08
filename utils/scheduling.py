from datetime import timedelta, timezone, datetime

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from services.user import UserService
from utils import send_reminder_to_user, send_message_to_all_users


jobstores = {
    'reminders': MemoryJobStore(),
    'broadcasts': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}

scheduler = AsyncIOScheduler(jobstores=jobstores)


async def schedule_reminders():
    """
    Schedule daily reminders for all users based on their preferred time and time zone.

    This function:
    - Fetches all users from the database.
    - Removes any existing reminder jobs.
    - Schedules new reminder jobs for each user with a specified reminder time and time zone.

    Notes:
    - Each user's reminder time and time zone are used to schedule the job.
    - The job sends a reminder message to the user at the specified time.
    """
    user_service: UserService = UserService()

    users = await user_service.get_all_users()
    scheduler.remove_all_jobs(jobstore='reminders')
    for user in users:
        username = user.get('tg_login')
        reminder_time = user.get('reminder_time')
        user_tz_offset = user.get('time_zone')
        user_id = user.get('user_id')
        if reminder_time and user_tz_offset:
            user_tz = timezone(timedelta(hours=int(user_tz_offset)))
            scheduler.add_job(func=send_reminder_to_user, trigger='cron',
                              hour=reminder_time.hour, minute=reminder_time.minute,
                              timezone=user_tz,
                              kwargs={'user_id': user_id},
                              jobstore='reminders', name=f'Reminder for @{username} ({user_id})')


async def schedule_broadcast(date_time: datetime, text: str):
    """
    Schedule a broadcast message to all users at a specified date and time.

    Parameters:
    - date_time (datetime): The date and time to send the broadcast message.
    - text (str): The message text to broadcast.

    This function:
    - Creates a timezone-aware datetime object for the specified time.
    - Schedules a job to send the broadcast message at the specified date and time.
    """
    tz = timezone(timedelta(hours=3))
    date_time = date_time.replace(tzinfo=tz)
    trigger = DateTrigger(run_date=date_time)
    scheduler.add_job(func=send_message_to_all_users, trigger=trigger,
                      kwargs={'text': text},
                      jobstore='broadcasts', name=f'Broadcast {date_time.strftime("%H:%M (UTC+3) %d.%m.%Y")}')


async def delete_scheduled_broadcasts():
    """
    Delete all scheduled broadcast jobs.

    This function:
    - Removes all jobs from the 'broadcasts' jobstore.
    """
    scheduler.remove_all_jobs(jobstore='broadcasts')
