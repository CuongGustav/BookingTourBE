from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, datetime
from src.extension import db
from src.model.model_booking import Bookings, BookingStatusEnum
from src.model.model_coupon import Coupons
from src.model.model_tour_schedule import Tour_Schedules

#cancel bookings CONFIRMED but not fully paid 
def auto_cancel_unpaid_bookings(app):
    with app.app_context():
        try:
            today = date.today()
            bookings_to_cancel = db.session.query(Bookings).join(
                Tour_Schedules, Bookings.schedule_id == Tour_Schedules.schedule_id
            ).filter(
                Bookings.status == BookingStatusEnum.CONFIRMED,
                Bookings.is_full_payment == False,
                Tour_Schedules.departure_date <= today
            ).all()
            
            if not bookings_to_cancel:
                print(f"[{datetime.now()}] Không có booking chưa thanh toán đủ cần hủy")
                return
            
            count = 0
            for booking in bookings_to_cancel:
                schedule = booking.schedule
                total_passengers = booking.num_adults + booking.num_children + booking.num_infants
                schedule.booked_seats -= total_passengers

                booking.status = BookingStatusEnum.CANCELLED.value
                booking.cancellation_reason = "Tự động hủy do chưa thanh toán đủ khi đến ngày khởi hành"
                booking.cancelled_at = datetime.now()
                count += 1
            
            db.session.commit()
            print(f"[{datetime.now()}] Đã hủy {count} booking chưa thanh toán đủ")
            
        except Exception as e:
            db.session.rollback()
            print(f"[{datetime.now()}] Lỗi khi hủy booking: {str(e)}")

#complete bookings CONFIRMED 
def update_completed_bookings(app):
    with app.app_context():
        try:
            today = date.today()
            
            bookings_to_complete = db.session.query(Bookings).join(
                Tour_Schedules, Bookings.schedule_id == Tour_Schedules.schedule_id
            ).filter(
                Bookings.status == BookingStatusEnum.CONFIRMED,
                Bookings.is_full_payment == True,
                Tour_Schedules.return_date < today
            ).all()
            
            if not bookings_to_complete:
                print(f"[{datetime.now()}] Không có booking cần cập nhật")
                return
            
            count = 0
            for booking in bookings_to_complete:
                booking.status = BookingStatusEnum.COMPLETED.value
                count += 1
            
            db.session.commit()
            print(f"[{datetime.now()}] Cập nhật {count} booking -> COMPLETED")
            
        except Exception as e:
            db.session.rollback()
            print(f"[{datetime.now()}] Lỗi: {str(e)}")

def deactivate_expired_coupons(app):
    with app.app_context():
        try:
            now = datetime.now()
            updated_count = (
                db.session.query(Coupons)
                .filter(
                    Coupons.valid_to < now,
                    Coupons.is_active == True
                )
                .update({"is_active": False})
            )

            if updated_count > 0:
                db.session.commit()
                print(f"[{now}] Đã tắt {updated_count} coupon hết hạn")
            else:
                print(f"[{now}] Không có coupon nào hết hạn cần tắt")

        except Exception as e:
            db.session.rollback()
            print(f"[{now}] Lỗi khi tắt coupon hết hạn: {str(e)}")

def init_scheduler(app):
    try:
        from pytz import timezone
        vietnam_tz = timezone('Asia/Ho_Chi_Minh')
        
        scheduler = BackgroundScheduler(timezone=vietnam_tz)
        
        scheduler.add_job(
            func=lambda: auto_cancel_unpaid_bookings(app),  
            trigger="cron",
            hour=0,
            minute=1,
            timezone=vietnam_tz,
            id="auto_cancel_unpaid_bookings",
            name="Tự động hủy booking chưa thanh toán đủ",
            replace_existing=True
        )

        scheduler.add_job(
            func=lambda: update_completed_bookings(app),  
            trigger="cron",
            hour=0,
            minute=5,
            timezone=vietnam_tz,
            id="update_completed_bookings",
            name="Cập nhật booking đã hoàn thành",
            replace_existing=True
        )

        scheduler.add_job(
            func=lambda: deactivate_expired_coupons(app),
            trigger="cron",
            hour=0,
            minute=10,
            timezone=vietnam_tz,
            id="deactivate_expired_coupons",
            name="Tắt các coupon đã hết hạn",
            replace_existing=True,
        )
        
        scheduler.start()
        print("Scheduler: Chạy mỗi ngày lúc 0:01, 0:05, 0:10")
        
        import atexit
        atexit.register(lambda: scheduler.shutdown())
        
        return scheduler
        
    except Exception as e:
        print(f"Lỗi scheduler: {str(e)}")
        return None