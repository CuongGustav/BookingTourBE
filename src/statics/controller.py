from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.statics.services import (general_statics_service, get_daily_revenue_trend_service, get_monthly_revenue_trend_service, 
                                  get_revenue_by_date_range_service, get_revenue_by_day_service, get_revenue_by_month_service, 
                                  get_revenue_by_year_service, get_yearly_revenue_trend_service)

statics = Blueprint("statics", __name__)

# general statics
@statics.route("/admin/general-statics", methods=["GET"])
@jwt_required()
@require_role('qcadmin')
def general_statics():
    return general_statics_service()

# revenue by day
@statics.route("/admin/revenue/day", methods=["GET"])
@jwt_required()
@require_role('qcadmin')
def get_revenue_by_day():
    try:
        year = int(request.args.get('year'))
        month = int(request.args.get('month'))
        day = int(request.args.get('day'))
    except (TypeError, ValueError):
        return {
            "message": "Thiếu hoặc sai định dạng year, month, day",
            "data": None
        }, 400
    
    return get_revenue_by_day_service(year, month, day)

# revenue by month
@statics.route("/admin/revenue/month", methods=["GET"])
@jwt_required()
@require_role('qcadmin')
def revenue_by_month():
    try:
        year = int(request.args.get('year'))
        month = int(request.args.get('month'))
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Thiếu hoặc sai định dạng year, month",
            "data": None
        }, 400
    return get_revenue_by_month_service(year, month)

# revenue by year
@statics.route("/admin/revenue/year", methods=["GET"])
@jwt_required()
@require_role('qcadmin')
def revenue_by_year():
    try:
        year = int(request.args.get('year'))
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Thiếu hoặc sai định dạng year",
            "data": None
        }, 400
    
    return get_revenue_by_year_service(year)

# revenue by date range
@statics.route("/admin/revenue/range", methods=["GET"])
@jwt_required()
@require_role('qcadmin')
def revenue_by_date_range():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return {
            "success": False,
            "message": "Thiếu start_date hoặc end_date",
            "data": None
        }, 400
    
    return get_revenue_by_date_range_service(start_date, end_date)

#get revenue all day in month
@statics.route("/admin/revenue/trend/daily", methods=["GET"])
@jwt_required()
@require_role('qcadmin')
def daily_revenue_trend():
    try:
        year = int(request.args.get('year'))
        month = int(request.args.get('month'))
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Thiếu hoặc sai định dạng year, month",
            "data": None
        }, 400
    return get_daily_revenue_trend_service(year, month)

#get revenue all month in year
@statics.route("/admin/revenue/trend/monthly", methods=["GET"])
@jwt_required()
@require_role('qcadmin')
def monthly_revenue_trend():
    try:
        year = int(request.args.get('year'))
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Thiếu hoặc sai định dạng year",
            "data": None
        }, 400
    
    return get_monthly_revenue_trend_service(year)

@statics.route("/admin/revenue/trend/yearly", methods=["GET"])
@jwt_required()
@require_role('qcadmin')
def yearly_revenue_trend():
    return get_yearly_revenue_trend_service()