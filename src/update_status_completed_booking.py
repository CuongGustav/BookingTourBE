from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, datetime
from src.extension import db
from src.model.model_booking import Bookings, BookingStatusEnum
from src.model.model_tour_schedule import Tour_Schedules

def update_completed_bookings(app):
    with app.app_context():
        try:
            today = date.today()
            
            bookings_to_complete = db.session.query(Bookings).join(
                Tour_Schedules, Bookings.schedule_id == Tour_Schedules.schedule_id
            ).filter(
                Bookings.status == BookingStatusEnum.CONFIRMED,
                Tour_Schedules.return_date < today
            ).all()
            
            if not bookings_to_complete:
                print(f"[{datetime.now()}] Không có booking cần cập nhật")
                return
            
            count = 0
            for booking in bookings_to_complete:
                booking.status = BookingStatusEnum.COMPLETED
                count += 1
            
            db.session.commit()
            print(f"[{datetime.now()}] Cập nhật {count} booking -> COMPLETED")
            
        except Exception as e:
            db.session.rollback()
            print(f"[{datetime.now()}] Lỗi: {str(e)}")

def init_scheduler(app):
    try:
        from pytz import timezone
        vietnam_tz = timezone('Asia/Ho_Chi_Minh')
        
        scheduler = BackgroundScheduler(timezone=vietnam_tz)
        
        scheduler.add_job(
            func=lambda: update_completed_bookings(app),  
            trigger="cron",
            hour=0,
            minute=0,
            timezone=vietnam_tz,
            id="update_completed_bookings",
            name="Cập nhật booking đã hoàn thành",
            replace_existing=True
        )
        
        scheduler.start()
        print("Scheduler: Chạy mỗi ngày lúc 0:00")
        
        import atexit
        atexit.register(lambda: scheduler.shutdown())
        
        return scheduler
        
    except Exception as e:
        print(f"Lỗi scheduler: {str(e)}")
        return None