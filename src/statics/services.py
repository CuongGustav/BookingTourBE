from datetime import date, datetime
from urllib import request
from flask import jsonify
from sqlalchemy import DECIMAL, case, desc, func
from src.model.model_booking import Bookings, BookingStatusEnum
from src.model.model_destination import Destinations
from src.model.model_tour import Tours
from src.model.model_account import Accounts, RoleEnum
from src.model.model_review import Reviews
from src.model.model_payment import Payments, PaymentStatusEnum
from src.extension import db
from src.model.model_tour_destination import Tour_Destinations
from src.model.model_tour_schedule import ScheduleStatusEnum, Tour_Schedules

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
from datetime import datetime, date
import calendar
from flask import jsonify
from sqlalchemy import func
from src.extension import db
from src.model.model_payment import Payments, PaymentStatusEnum

def get_daily_revenue_trend_service(year: int, month: int):
    try:
        _, num_days = calendar.monthrange(year, month)
        
        results = []
        success_statuses = [PaymentStatusEnum.COMPLETED.value] 
        refunded_statuses = [PaymentStatusEnum.REFUNDED.value]  
        
        for day in range(1, num_days + 1):
            current_date = date(year, month, day)
            
            completed_query = db.session.query(
                func.coalesce(func.sum(Payments.amount), 0)
            ).filter(
                func.date(Payments.created_at) == current_date, 
                Payments.status == PaymentStatusEnum.COMPLETED.value
            ).scalar() or 0
            
            refunded_query = db.session.query(
                func.coalesce(func.sum(Payments.amount), 0)
            ).filter(
                func.date(Payments.created_at) == current_date,
                Payments.status == PaymentStatusEnum.REFUNDED.value
            ).scalar() or 0
            
            net_revenue = float(completed_query) - float(refunded_query)
            
            results.append({
                "date": current_date.isoformat(),
                "period_label": f"{day:02d}/{month:02d}",
                "completed": float(completed_query),
                "refunded": float(refunded_query),
                "net_revenue": net_revenue
            })
        
        return {
            "success": True,
            "message": "Lấy xu hướng doanh thu hàng ngày thành công",
            "data": {
                "period_type": "daily",
                "year": year,
                "month": month,
                "results": results
            }
        }, 200
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi khi lấy xu hướng doanh thu hàng ngày: {str(e)}",
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
    
#static top tour by booking
def get_top_tours_by_booking_service():
    try:
        limit = 5
        success_statuses = [
            BookingStatusEnum.CONFIRMED.value,
            BookingStatusEnum.COMPLETED.value
        ]

        # Top tours by bookings
        top_tours_query = db.session.query(
            Tours.tour_id,
            Tours.title,
            func.count(Bookings.booking_id).label('booking_count'),
            func.sum(Bookings.final_price).label('total_revenue')
        ).join(Bookings, Tours.tour_id == Bookings.tour_id
        ).filter(Bookings.status.in_(success_statuses)
        ).group_by(Tours.tour_id, Tours.title
        ).order_by(desc('booking_count'), desc('total_revenue')
        ).limit(limit).all()

        top_tours = [
            {
                'tour_id': t.tour_id,
                'title': t.title,
                'booking_count': t.booking_count,
                'total_revenue': float(t.total_revenue) if t.total_revenue else 0
            } for t in top_tours_query
        ]

        # Average passengers per tour
        subq = db.session.query(
            Bookings.tour_id,
            func.sum(Bookings.num_adults + Bookings.num_children + Bookings.num_infants).label('total_passengers')
        ).filter(Bookings.status.in_(success_statuses)
        ).group_by(Bookings.tour_id).subquery()

        avg_passengers = db.session.query(
            func.avg(subq.c.total_passengers)
        ).scalar() or 0.0

        # Average fill rate
        avg_fill_rate = db.session.query(
            func.avg(
                (func.cast(Tour_Schedules.booked_seats, DECIMAL) / Tour_Schedules.available_seats) * 100
            )
        ).filter(
            Tour_Schedules.available_seats > 0,
            Tour_Schedules.status != ScheduleStatusEnum.CANCELLED.value
        ).scalar() or 0.0

        data = {
            'top_tours': top_tours,
            'average_passengers_per_tour': float(avg_passengers),
            'average_fill_rate': float(avg_fill_rate)
        }

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi: {str(e)}",
            "data": None
        }, 500
    
#static top destinations and regions by booking
def get_top_destinations_service():
    try:
        success_statuses = [
            BookingStatusEnum.CONFIRMED.value,
            BookingStatusEnum.COMPLETED.value
        ]
        # Top 8 destinations
        top_destinations_query = db.session.query(
            Destinations.destination_id,
            Destinations.name,
            Destinations.country,
            Destinations.region,
            func.count(Bookings.booking_id).label('booking_count'),
            func.sum(Bookings.final_price).label('total_revenue')
        ).join(
            Tour_Destinations, Destinations.destination_id == Tour_Destinations.destination_id
        ).join(
            Tours, Tour_Destinations.tour_id == Tours.tour_id
        ).join(
            Bookings, Tours.tour_id == Bookings.tour_id
        ).filter(
            Bookings.status.in_(success_statuses),
            Destinations.is_active == True
        ).group_by(
            Destinations.destination_id,
            Destinations.name,
            Destinations.country,
            Destinations.region
        ).order_by(
            desc('booking_count'),
            desc('total_revenue')
        ).limit(8).all()
        
        top_destinations = [
            {
                'destination_id': d.destination_id,
                'name': d.name,
                'country': d.country,
                'region': d.region,
                'booking_count': d.booking_count,
                'total_revenue': float(d.total_revenue) if d.total_revenue else 0
            } for d in top_destinations_query
        ]
        
        # Top region by bookings
        top_regions_query = db.session.query(
            Destinations.region,
            func.count(Bookings.booking_id).label('booking_count'),
            func.sum(Bookings.final_price).label('total_revenue')
        ).join(
            Tour_Destinations, Destinations.destination_id == Tour_Destinations.destination_id
        ).join(
            Tours, Tour_Destinations.tour_id == Tours.tour_id
        ).join(
            Bookings, Tours.tour_id == Bookings.tour_id
        ).filter(
            Bookings.status.in_(success_statuses),
            Destinations.is_active == True,
            Destinations.region.isnot(None),
            Destinations.region != ''
        ).group_by(
            Destinations.region
        ).order_by(
            desc('booking_count'),
            desc('total_revenue')
        ).all()
        
        top_regions = [
            {
                'region': r.region,
                'booking_count': r.booking_count,
                'total_revenue': float(r.total_revenue) if r.total_revenue else 0
            } for r in top_regions_query
        ]
        
        most_popular_region = top_regions[0] if top_regions else None
        
        data = {
            'top_destinations': top_destinations,
            'top_regions': top_regions,
            'most_popular_region': most_popular_region
        }
        
        return {
            "success": True,
            "message": "Lấy thống kê điểm đến thành công",
            "data": data
        }, 200
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Lỗi: {str(e)}",
            "data": None
        }, 500