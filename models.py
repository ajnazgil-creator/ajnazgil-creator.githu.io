from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    avatar = db.Column(db.String(256), default='default_avatar.png')
    company = db.Column(db.String(128))
    passport_series = db.Column(db.String(20))
    driver_license = db.Column(db.String(30))
    address = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    bookings = db.relationship('Booking', backref='user', lazy='dynamic')
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def unread_notifications_count(self):
        return self.notifications.filter_by(is_read=False).count()


class Truck(db.Model):
    __tablename__ = 'trucks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    model = db.Column(db.String(64), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    payload = db.Column(db.Float, nullable=False)
    body_type = db.Column(db.String(64), nullable=False)
    volume = db.Column(db.Float)
    engine_volume = db.Column(db.Float)
    engine_power = db.Column(db.Integer)
    fuel_type = db.Column(db.String(32), default='Дизель')
    fuel_consumption = db.Column(db.Float)
    transmission = db.Column(db.String(32))
    color = db.Column(db.String(32))
    mileage = db.Column(db.Integer, default=0)
    price_per_day = db.Column(db.Float, nullable=False)
    price_with_driver = db.Column(db.Float)
    deposit = db.Column(db.Float, default=0)
    image = db.Column(db.String(256), default='truck_default.jpg')
    description = db.Column(db.Text)
    features = db.Column(db.Text)
    status = db.Column(db.String(32), default='available')
    is_featured = db.Column(db.Boolean, default=False)
    dimensions_l = db.Column(db.Float)
    dimensions_w = db.Column(db.Float)
    dimensions_h = db.Column(db.Float)
    max_speed = db.Column(db.Integer)
    drive_type = db.Column(db.String(32))
    axles = db.Column(db.Integer, default=2)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('Booking', backref='truck', lazy='dynamic')
    reviews = db.relationship('Review', backref='truck', lazy='dynamic')

    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def review_count(self):
        return self.reviews.count()

    def is_available_for(self, start_date, end_date):
        conflicting = Booking.query.filter(
            Booking.truck_id == self.id,
            Booking.status.in_(['confirmed', 'active']),
            Booking.start_date < end_date,
            Booking.end_date > start_date
        ).count()
        return conflicting == 0 and self.status == 'available'


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    truck_id = db.Column(db.Integer, db.ForeignKey('trucks.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer)
    base_price = db.Column(db.Float)
    with_driver = db.Column(db.Boolean, default=False)
    with_insurance = db.Column(db.Boolean, default=False)
    insurance_price = db.Column(db.Float, default=0)
    driver_price = db.Column(db.Float, default=0)
    total_price = db.Column(db.Float, nullable=False)
    deposit_paid = db.Column(db.Float, default=0)
    status = db.Column(db.String(32), default='pending')
    payment_status = db.Column(db.String(32), default='unpaid')
    pickup_location = db.Column(db.String(256))
    return_location = db.Column(db.String(256))
    notes = db.Column(db.Text)
    admin_notes = db.Column(db.Text)
    contract_number = db.Column(db.String(32), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def duration_days(self):
        return (self.end_date - self.start_date).days


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    truck_id = db.Column(db.Integer, db.ForeignKey('trucks.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(32), default='info')
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SiteSettings(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(256))
