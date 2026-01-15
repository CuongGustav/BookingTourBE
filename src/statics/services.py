from datetime import date, datetime
from sqlalchemy import case, func
from src.model.model_booking import Bookings, BookingStatusEnum
from src.model.model_tour import Tours
from src.model.model_account import Accounts, RoleEnum
from src.model.model_review import Reviews
from src.model.model_payment import Payments, PaymentStatusEnum
from src.extension import db
from src.model.model_tour_schedule import Tour_Schedules

#general statics
def general_statics_service():
    try:
        # total booking
        total_bookings = db.session.query(func.count(Bookings.booking_id)).scalar() or 0
        
        #revenue - doanh thu
        total_completed = db.session.query(
            func.coalesce(func.sum(Payments.amount), 0)
        ).join(
            Bookings, Bookings.booking_id == Payments.booking_id
        ).filter(
            Payments.status == PaymentStatusEnum.COMPLETED.value
        ).scalar() or 0
        
        total_refunded = db.session.query(
            func.coalesce(func.sum(Payments.amount), 0)
        ).filter(
            Payments.status == PaymentStatusEnum.REFUNDED.value
        ).scalar() or 0
        
        total_revenue = float(total_completed) - float(total_refunded)
        
        #sum tour is active
        total_tours = db.session.query(
            func.count(Tours.tour_id)
        ).filter(
            Tours.is_active == True
        ).scalar() or 0
        
        #sum customer
        total_customers = db.session.query(
            func.coalesce(func.sum(Tour_Schedules.booked_seats), 0)
        ).scalar() or 0
        
        # sum review
        total_reviews = db.session.query(func.count(Reviews.review_id)).scalar() or 0
        
        # proportion cancel booking (%)
        cancelled_bookings = db.session.query(
            func.count(Bookings.booking_id)
        ).filter(
            Bookings.status == BookingStatusEnum.CANCELLED.value
        ).scalar() or 0
        
        cancellation_rate = (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
        
        return {
                "total_bookings": total_bookings,
                "total_revenue": round(total_revenue, 2),
                "total_tours": total_tours,
                "total_customers": total_customers,
                "total_reviews": total_reviews,
                "cancellation_rate": round(cancellation_rate, 2)
        } , 200
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi khi lấy thống kê: {str(e)}",
            "data": None
        }, 500
    
#get revenue day
def get_revenue_by_day_service(year, month, day):
    try:
        target_date = date(year, month, day)
        
        # Query COMPLETED
        completed = db.session.query(
            func.sum(Payments.amount)
        ).filter(
            Payments.status == PaymentStatusEnum.COMPLETED.value,
            func.date(Payments.created_at) == target_date
        ).scalar() or 0
        
        # Query REFUNDED 
        refunded = db.session.query(
            func.sum(Payments.amount)
        ).filter(
            Payments.status == PaymentStatusEnum.REFUNDED.value,
            func.date(Payments.created_at) == target_date
        ).scalar() or 0
        
        # Query count payment
        total_transactions = db.session.query(
            func.count(Payments.payment_id)
        ).filter(
            func.date(Payments.created_at) == target_date
        ).scalar() or 0
        
        net_revenue = float(completed) - float(refunded)
        
        return {
            "message": "Lấy thống kê doanh thu theo ngày thành công",
            "data": {
                "period_type": "day",
                "period_label": f"{day:02d}/{month:02d}/{year}",
                "date": str(target_date),
                "completed": round(float(completed), 2),
                "refunded": round(float(refunded), 2),
                "net_revenue": round(net_revenue, 2),
                "total_transactions": total_transactions
            }
        }, 200
        
    except ValueError as e:
        return {
            "message": f"Ngày tháng không hợp lệ: {str(e)}",
            "data": None
        }, 400
    except Exception as e:
        return {
            "message": f"Lỗi: {str(e)}",
            "data": None
        }, 500
    
#get revenue month
def get_revenue_by_month_service(year, month):
    try:
        # Query COMPLETED 
        completed = db.session.query(
            func.sum(Payments.amount)
        ).filter(
            Payments.status == PaymentStatusEnum.COMPLETED.value,
            func.extract('year', Payments.created_at) == year,
            func.extract('month', Payments.created_at) == month
        ).scalar() or 0
        
        # Query REFUNDED
        refunded = db.session.query(
            func.sum(Payments.amount)
        ).filter(
            Payments.status == PaymentStatusEnum.REFUNDED.value,
            func.extract('year', Payments.created_at) == year,
            func.extract('month', Payments.created_at) == month
        ).scalar() or 0
        
        # Query count payment
        total_transactions = db.session.query(
            func.count(Payments.payment_id)
        ).filter(
            func.extract('year', Payments.created_at) == year,
            func.extract('month', Payments.created_at) == month
        ).scalar() or 0
        
        net_revenue = float(completed) - float(refunded)
        
        return {
            "success": True,
            "message": "Lấy thống kê doanh thu theo tháng thành công",
            "data": {
                "period_type": "month",
                "period_label": f"{month:02d}/{year}",
                "year": year,
                "month": month,
                "completed": round(float(completed), 2),
                "refunded": round(float(refunded), 2),
                "net_revenue": round(net_revenue, 2),
                "total_transactions": total_transactions
            }
        }, 200
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi: {str(e)}",
            "data": None
        }, 500

#get revenue year
def get_revenue_by_year_service(year):
    try:
        # Query COMPLETED
        completed = db.session.query(
            func.sum(Payments.amount)
        ).filter(
            Payments.status == PaymentStatusEnum.COMPLETED.value,
            func.extract('year', Payments.created_at) == year
        ).scalar() or 0
        
        # Query REFUNDED 
        refunded = db.session.query(
            func.sum(Payments.amount)
        ).filter(
            Payments.status == PaymentStatusEnum.REFUNDED.value,
            func.extract('year', Payments.created_at) == year
        ).scalar() or 0
        
        # Query count
        total_transactions = db.session.query(
            func.count(Payments.payment_id)
        ).filter(
            func.extract('year', Payments.created_at) == year
        ).scalar() or 0
        
        net_revenue = float(completed) - float(refunded)
        
        return {
            "success": True,
            "message": "Lấy thống kê doanh thu theo năm thành công",
            "data": {
                "period_type": "year",
                "period_label": str(year),
                "year": year,
                "completed": round(float(completed), 2),
                "refunded": round(float(refunded), 2),
                "net_revenue": round(net_revenue, 2),
                "total_transactions": total_transactions
            }
        }, 200
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi: {str(e)}",
            "data": None
        }, 500
    
#get revenue date range
def get_revenue_by_date_range_service(start_date_str, end_date_str):
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        if start_date > end_date:
            return {
                "success": False,
                "message": "Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc",
                "data": None
            }, 400
        
        # Query COMPLETED 
        completed = db.session.query(
            func.sum(Payments.amount)
        ).filter(
            Payments.status == PaymentStatusEnum.COMPLETED.value,
            func.date(Payments.created_at) >= start_date,
            func.date(Payments.created_at) <= end_date
        ).scalar() or 0
        
        # Query REFUNDED 
        refunded = db.session.query(
            func.sum(Payments.amount)
        ).filter(
            Payments.status == PaymentStatusEnum.REFUNDED.value,
            func.date(Payments.created_at) >= start_date,
            func.date(Payments.created_at) <= end_date
        ).scalar() or 0
        
        # Query count payment
        total_transactions = db.session.query(
            func.count(Payments.payment_id)
        ).filter(
            func.date(Payments.created_at) >= start_date,
            func.date(Payments.created_at) <= end_date
        ).scalar() or 0
        
        net_revenue = float(completed) - float(refunded)
        
        return {
            "success": True,
            "message": "Lấy thống kê doanh thu theo khoảng thời gian thành công",
            "data": {
                "period_type": "custom",
                "period_label": f"{start_date_str} đến {end_date_str}",
                "start_date": start_date_str,
                "end_date": end_date_str,
                "completed": round(float(completed), 2),
                "refunded": round(float(refunded), 2),
                "net_revenue": round(net_revenue, 2),
                "total_transactions": total_transactions
            }
        }, 200
        
    except ValueError:
        return {
            "success": False,
            "message": "Định dạng ngày không hợp lệ. Sử dụng YYYY-MM-DD",
            "data": None
        }, 400
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi: {str(e)}",
            "data": None
        }, 500

#get revenue all day in month
def get_daily_revenue_trend_service(year, month):
    try:
        results = db.session.query(
            func.date(Payments.created_at).label('date'),
            func.sum(
                case(
                    (Payments.status == PaymentStatusEnum.COMPLETED.value, Payments.amount),
                    else_=0
                )
            ).label('completed'),
            func.sum(
                case(
                    (Payments.status == PaymentStatusEnum.REFUNDED.value, Payments.amount),
                    else_=0
                )
            ).label('refunded')
        ).filter(
            func.extract('year', Payments.created_at) == year,
            func.extract('month', Payments.created_at) == month
        ).group_by(
            func.date(Payments.created_at)
        ).order_by(
            func.date(Payments.created_at)
        ).all()
        
        data = []
        for row in results:
            completed = float(row.completed or 0)
            refunded = float(row.refunded or 0)
            net_revenue = completed - refunded
            
            data.append({
                "date": str(row.date),
                "period_label": row.date.strftime("%d/%m"),
                "completed": round(completed, 2),
                "refunded": round(refunded, 2),
                "net_revenue": round(net_revenue, 2)
            })
        
        return {
            "success": True,
            "message": "Lấy xu hướng doanh thu theo ngày thành công",
            "data": {
                "period_type": "daily",
                "year": year,
                "month": month,
                "results": data
            }
        }, 200
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi: {str(e)}",
            "data": None
        }, 500

#get revenue all month in year
def get_monthly_revenue_trend_service(year):
    try:
        results = db.session.query(
            func.extract('month', Payments.created_at).label('month'),
            func.sum(
                case(
                    (Payments.status == PaymentStatusEnum.COMPLETED.value, Payments.amount),
                    else_=0
                )
            ).label('completed'),
            func.sum(
                case(
                    (Payments.status == PaymentStatusEnum.REFUNDED.value, Payments.amount),
                    else_=0
                )
            ).label('refunded')
        ).filter(
            func.extract('year', Payments.created_at) == year
        ).group_by(
            func.extract('month', Payments.created_at)
        ).order_by(
            func.extract('month', Payments.created_at)
        ).all()
        
        data = []
        for row in results:
            completed = float(row.completed or 0)
            refunded = float(row.refunded or 0)
            net_revenue = completed - refunded
            
            data.append({
                "month": int(row.month),
                "year": year,
                "period_label": f"Tháng {int(row.month)}",
                "completed": round(completed, 2),
                "refunded": round(refunded, 2),
                "net_revenue": round(net_revenue, 2)
            })
        return {
            "success": True,
            "message": "Lấy xu hướng doanh thu theo tháng thành công",
            "data": {
                "period_type": "monthly",
                "year": year,
                "results": data
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi: {str(e)}",
            "data": None
        }, 500

#get revenue in 5 year
def get_yearly_revenue_trend_service(limit=5):
    try:
        results = db.session.query(
            func.extract('year', Payments.created_at).label('year'),
            func.sum(
                case(
                    (Payments.status == PaymentStatusEnum.COMPLETED.value, Payments.amount),
                    else_=0
                )
            ).label('completed'),
            func.sum(
                case(
                    (Payments.status == PaymentStatusEnum.REFUNDED.value, Payments.amount),
                    else_=0
                )
            ).label('refunded')
        ).group_by(
            func.extract('year', Payments.created_at)
        ).order_by(
            func.extract('year', Payments.created_at).desc()
        ).limit(limit).all()
        
        data = []
        for row in reversed(results):  
            completed = float(row.completed or 0)
            refunded = float(row.refunded or 0)
            net_revenue = completed - refunded
            
            data.append({
                "year": int(row.year),
                "period_label": str(int(row.year)),
                "completed": round(completed, 2),
                "refunded": round(refunded, 2),
                "net_revenue": round(net_revenue, 2)
            })
        return {
            "success": True,
            "message": "Lấy xu hướng doanh thu theo năm thành công",
            "data": {
                "period_type": "yearly",
                "results": data
            }
        }, 200
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi: {str(e)}",
            "data": None
        }, 500
    
#