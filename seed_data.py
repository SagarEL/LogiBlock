from app import app, db
from models import Warehouse, Route, RouteWarehouse, User, Shipment
import random
from werkzeug.security import generate_password_hash

def seed_data():
    with app.app_context():
        # Create 25 warehouses across India
        warehouses_data = [
            ("Mumbai Central Hub", "WH-MUM-01", 19.0760, 72.8777),
            ("Delhi North Distribution", "WH-DEL-01", 28.7041, 77.1025),
            ("Bangalore Tech Park", "WH-BLR-01", 12.9716, 77.5946),
            ("Chennai Port Terminal", "WH-MAA-01", 13.0827, 80.2707),
            ("Kolkata East Logistics", "WH-CCU-01", 22.5726, 88.3639),
            ("Hyderabad Pharma Hub", "WH-HYD-01", 17.3850, 78.4867),
            ("Ahmedabad Industrial", "WH-AMD-01", 23.0225, 72.5714),
            ("Pune Auto Hub", "WH-PNQ-01", 18.5204, 73.8567),
            ("Jaipur Transit Center", "WH-JAI-01", 26.9124, 75.7873),
            ("Surat Textile Hub", "WH-STV-01", 21.1702, 72.8311),
            # Newly added locations below
            ("Bangalore Electronic City", "WH-BLR-02", 12.8452, 77.6602),
            ("Bangalore Whitefield Hub", "WH-BLR-03", 12.9698, 77.7499),
            ("Noida Sector 62 Logistics", "WH-NOI-01", 28.6208, 77.3639),
            ("Gurgaon Transit Center", "WH-GUR-01", 28.4906, 77.0886),
            ("Lucknow Gomti Nagar Hub", "WH-LKO-01", 26.8528, 80.9940),
            ("Bhopal Arera Distribution", "WH-BHO-01", 23.2146, 77.4338),
            ("Indore Pithampur Park", "WH-IND-01", 22.6157, 75.6690),
            ("Kochi Port Cargo Hub", "WH-COK-01", 9.9654, 76.2625),
            ("Trivandrum Sort Center", "WH-TRV-01", 8.5241, 76.9366),
            ("Guwahati Gateway Hub", "WH-GAU-01", 26.1445, 91.7362),
            ("Chandigarh Industrial", "WH-IXC-01", 30.7046, 76.8013),
            ("Ludhiana Transport Nagar", "WH-LUH-01", 30.9010, 75.8573),
            ("Visakhapatnam Port Hub", "WH-VTZ-01", 17.6868, 83.2185),
            ("Coimbatore Peelamedu Facility", "WH-CJB-01", 11.0261, 77.0270),
            ("Nagpur Zero Mile Central", "WH-NAG-01", 21.1458, 79.0882)
        ]
        
        warehouses = []
        for name, code, lat, lng in warehouses_data:
            wh = Warehouse.query.filter_by(warehouse_code=code).first()
            if not wh:
                wh = Warehouse(warehouse_id=code, warehouse_name=name, location=name, warehouse_code=code, lat=lat, lng=lng)
                db.session.add(wh)
            warehouses.append(wh)
            
        db.session.commit()
        print("10 Warehouses seeded.")

        # Users are now seeded comprehensively in app.py

        # We will create routes and shipments via the browser to test the UI, or just seed routes and test shipments.
        # Let's seed 1 route to test the rest via browser.
        # Or better, just let the subagent create a route.

if __name__ == '__main__':
    seed_data()
