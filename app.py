import os
import random
import string
from datetime import datetime, date, timedelta
from functools import wraps
from io import BytesIO

from flask import (Flask, render_template, redirect, url_for, flash,
                   request, jsonify, send_file, abort, session)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from sqlalchemy import func, extract

from config import config
from models import db, User, Truck, Booking, Review, Notification, SiteSettings

app = Flask(__name__)
app.config.from_object(config[os.environ.get('FLASK_ENV', 'default')])

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def generate_contract_number():
    return 'IF-' + ''.join(random.choices(string.digits, k=8))

def create_notification(user_id, title, message, ntype='info', link=None):
    n = Notification(user_id=user_id, title=title, message=message, type=ntype, link=link)
    db.session.add(n)

TRUCKS_DATA = [
    {
        'name': 'Isuzu Forward FRR 90 Бортовой',
        'model': 'FRR 90',
        'year': 2022,
        'payload': 7.0,
        'body_type': 'Бортовой',
        'volume': 30.0,
        'engine_volume': 7.8,
        'engine_power': 280,
        'fuel_type': 'Дизель',
        'fuel_consumption': 18.5,
        'transmission': 'Механика 6 ст.',
        'color': 'Белый',
        'mileage': 45000,
        'price_per_day': 8500.0,
        'price_with_driver': 12000.0,
        'deposit': 25000.0,
        'image': 'truck1.jpg',
        'description': 'Надёжный бортовой грузовик Isuzu Forward FRR 90 — идеальное решение для перевозки строительных материалов, оборудования и паллетированных грузов. Оснащён усиленной рамой и расширенной платформой. Отличная маневренность в городских условиях при высокой грузоподъёмности.',
        'features': 'ABS,ESP,Кондиционер,Подогрев сидений,Камера заднего вида,Тахограф,GPS-трекер,Пневмоподвеска',
        'is_featured': True,
        'dimensions_l': 7.5, 'dimensions_w': 2.45, 'dimensions_h': 2.4,
        'max_speed': 120, 'drive_type': '4x2', 'axles': 2
    },
    {
        'name': 'Isuzu Forward FRR 34 Рефрижератор',
        'model': 'FRR 34',
        'year': 2023,
        'payload': 5.0,
        'body_type': 'Рефрижератор',
        'volume': 22.0,
        'engine_volume': 5.2,
        'engine_power': 210,
        'fuel_type': 'Дизель',
        'fuel_consumption': 16.0,
        'transmission': 'Автомат 6 ст.',
        'color': 'Белый',
        'mileage': 28000,
        'price_per_day': 11000.0,
        'price_with_driver': 15500.0,
        'deposit': 35000.0,
        'image': 'truck2.jpg',
        'description': 'Рефрижераторный грузовик с холодильной установкой Carrier Supra. Поддерживает температуру от -25°C до +25°C. Идеален для транспортировки продуктов питания, медикаментов, цветов и других температурочувствительных грузов. Холодильный отсек с тремя независимыми зонами температуры.',
        'features': 'Холодильник Carrier,-25 до +25°C,3 температурные зоны,ABS,ESP,Кондиционер,GPS-трекер,Тахограф,Тепловой мониторинг',
        'is_featured': True,
        'dimensions_l': 6.8, 'dimensions_w': 2.4, 'dimensions_h': 2.6,
        'max_speed': 110, 'drive_type': '4x2', 'axles': 2
    },
    {
        'name': 'Isuzu Forward FVR 34 Самосвал',
        'model': 'FVR 34',
        'year': 2021,
        'payload': 10.0,
        'body_type': 'Самосвал',
        'volume': 8.0,
        'engine_volume': 9.8,
        'engine_power': 340,
        'fuel_type': 'Дизель',
        'fuel_consumption': 24.0,
        'transmission': 'Механика 8 ст.',
        'color': 'Оранжевый',
        'mileage': 62000,
        'price_per_day': 13500.0,
        'price_with_driver': 18000.0,
        'deposit': 40000.0,
        'image': 'truck3.jpg',
        'description': 'Мощный самосвал Isuzu Forward FVR 34 для перевозки сыпучих материалов: песок, щебень, грунт, строительный мусор. Кузов из высокопрочной стали с задней разгрузкой и боковыми бортами. Гидравлическая система подъёма с углом 50°. Незаменим на строительных площадках.',
        'features': 'Кузов из стали Hardox,Угол подъёма 50°,Защита от перегрузки,ABS,Ретардер,Кондиционер,GPS-трекер,Тахограф',
        'is_featured': True,
        'dimensions_l': 6.2, 'dimensions_w': 2.5, 'dimensions_h': 2.8,
        'max_speed': 100, 'drive_type': '4x2', 'axles': 2
    },
    {
        'name': 'Isuzu Forward FVZ 34 Тентованный',
        'model': 'FVZ 34',
        'year': 2022,
        'payload': 12.0,
        'body_type': 'Тентованный',
        'volume': 50.0,
        'engine_volume': 9.8,
        'engine_power': 380,
        'fuel_type': 'Дизель',
        'fuel_consumption': 26.0,
        'transmission': 'Автомат 8 ст.',
        'color': 'Серый',
        'mileage': 38000,
        'price_per_day': 15000.0,
        'price_with_driver': 20000.0,
        'deposit': 50000.0,
        'image': 'truck4.jpg',
        'description': 'Тентованный полуприцеп большой вместимости для перевозки генеральных грузов. Тент из ПВХ с усиленными дугами выдерживает снеговую нагрузку. Боковая загрузка по всей длине кузова. Идеально для мебели, текстиля, промышленного оборудования и паллетизированных грузов.',
        'features': 'Боковая загрузка,Тент ПВХ 650 г/м²,Стяжные ремни 16 шт.,Антипробуксовочная система,Кондиционер,GPS-трекер,Тахограф,Пневмоподвеска',
        'is_featured': False,
        'dimensions_l': 9.8, 'dimensions_w': 2.45, 'dimensions_h': 2.7,
        'max_speed': 120, 'drive_type': '6x2', 'axles': 3
    },
    {
        'name': 'Isuzu Forward FSR 90 Изотермический',
        'model': 'FSR 90',
        'year': 2023,
        'payload': 6.0,
        'body_type': 'Изотермический',
        'volume': 26.0,
        'engine_volume': 7.8,
        'engine_power': 250,
        'fuel_type': 'Дизель',
        'fuel_consumption': 17.0,
        'transmission': 'Механика 6 ст.',
        'color': 'Белый',
        'mileage': 15000,
        'price_per_day': 9500.0,
        'price_with_driver': 13500.0,
        'deposit': 30000.0,
        'image': 'truck5.jpg',
        'description': 'Изотермический фургон для перевозки грузов, требующих стабильной температуры без активного охлаждения. Пенополиуретановая изоляция 100мм обеспечивает сохранение температуры до 8 часов. Подходит для кондитерских изделий, напитков, бытовой химии и косметики.',
        'features': 'Изоляция 100мм,Алюминиевый пол,Гидравлический борт 1т,ABS,Кондиционер,GPS-трекер,Тахограф,Задняя камера',
        'is_featured': False,
        'dimensions_l': 7.2, 'dimensions_w': 2.4, 'dimensions_h': 2.55,
        'max_speed': 115, 'drive_type': '4x2', 'axles': 2
    },
    {
        'name': 'Isuzu Forward FRR 90L Манипулятор',
        'model': 'FRR 90L',
        'year': 2021,
        'payload': 7.0,
        'body_type': 'Кран-манипулятор',
        'volume': 18.0,
        'engine_volume': 7.8,
        'engine_power': 300,
        'fuel_type': 'Дизель',
        'fuel_consumption': 22.0,
        'transmission': 'Механика 6 ст.',
        'color': 'Жёлтый',
        'mileage': 55000,
        'price_per_day': 18000.0,
        'price_with_driver': 24000.0,
        'deposit': 60000.0,
        'image': 'truck6.jpg',
        'description': 'Грузовик с краном-манипулятором Fassi F110 — незаменим для погрузочно-разгрузочных работ без посторонней техники. Вылет стрелы 8 метров, грузоподъёмность крана 3 тонны. Работает с паллетами, металлоконструкциями, оборудованием. Аутригеры обеспечивают устойчивость при работе.',
        'features': 'Кран Fassi F110,Вылет 8м,Г/п крана 3т,Аутригеры,ABS,Кондиционер,GPS-трекер,Тахограф,Дистанционное управление',
        'is_featured': True,
        'dimensions_l': 8.0, 'dimensions_w': 2.45, 'dimensions_h': 3.5,
        'max_speed': 100, 'drive_type': '4x2', 'axles': 2
    },
    {
        'name': 'Isuzu Forward FVR 90 Фургон',
        'model': 'FVR 90',
        'year': 2022,
        'payload': 9.0,
        'body_type': 'Цельнометаллический фургон',
        'volume': 42.0,
        'engine_volume': 9.8,
        'engine_power': 320,
        'fuel_type': 'Дизель',
        'fuel_consumption': 21.0,
        'transmission': 'Автомат 6 ст.',
        'color': 'Белый',
        'mileage': 31000,
        'price_per_day': 12500.0,
        'price_with_driver': 17000.0,
        'deposit': 42000.0,
        'image': 'truck7.jpg',
        'description': 'Цельнометаллический фургон с увеличенным объёмом кузова. Идеален для перевозки бытовой техники, мебели, промышленных товаров и объёмных грузов. Алюминиевый пол с креплёжными профилями, двустворчатые задние двери и боковая распашная дверь. Высота погрузки 1000 мм.',
        'features': 'Алюминиевый пол,Боковая дверь,2-х створчатые задние двери,Стяжные ремни,ABS,ESP,Кондиционер,GPS-трекер,Тахограф',
        'is_featured': False,
        'dimensions_l': 8.8, 'dimensions_w': 2.45, 'dimensions_h': 2.8,
        'max_speed': 118, 'drive_type': '4x2', 'axles': 2
    },
    {
        'name': 'Isuzu Forward FTR 34 Цистерна',
        'model': 'FTR 34',
        'year': 2020,
        'payload': 8.0,
        'body_type': 'Цистерна',
        'volume': 10.0,
        'engine_volume': 9.8,
        'engine_power': 300,
        'fuel_type': 'Дизель',
        'fuel_consumption': 23.0,
        'transmission': 'Механика 8 ст.',
        'color': 'Стальной',
        'mileage': 78000,
        'price_per_day': 16000.0,
        'price_with_driver': 21500.0,
        'deposit': 55000.0,
        'image': 'truck8.jpg',
        'description': 'Автоцистерна из нержавеющей стали объёмом 10 000 литров. Применяется для перевозки питьевой воды, молока, соков, растительных масел и технических жидкостей. Оснащена насосом и системой мойки. Полностью соответствует нормам ДОПОГ для перевозки пищевых продуктов.',
        'features': 'Нержавеющая сталь,Насосная система,Система CIP мойки,Люки 3 шт.,ДОПОГ,ABS,GPS-трекер,Тахограф',
        'is_featured': False,
        'dimensions_l': 7.0, 'dimensions_w': 2.4, 'dimensions_h': 3.2,
        'max_speed': 100, 'drive_type': '4x2', 'axles': 2
    },
    {
        'name': 'Isuzu Forward EXR 51 Длинномер',
        'model': 'EXR 51',
        'year': 2023,
        'payload': 15.0,
        'body_type': 'Длинномер',
        'volume': 60.0,
        'engine_volume': 12.0,
        'engine_power': 450,
        'fuel_type': 'Дизель',
        'fuel_consumption': 30.0,
        'transmission': 'Автомат 12 ст.',
        'color': 'Белый',
        'mileage': 22000,
        'price_per_day': 22000.0,
        'price_with_driver': 29000.0,
        'deposit': 75000.0,
        'image': 'truck9.jpg',
        'description': 'Флагманский длинномер Isuzu Forward EXR 51 с максимальной грузоподъёмностью для магистральных перевозок. Удлинённая платформа позволяет перевозить трубы, металлопрокат, длинномерные конструкции до 12 метров. Пневматическая подвеска с электронным управлением обеспечивает комфорт при дальних рейсах.',
        'features': 'Платформа 12м,Пневмоподвеска,Retarder,Круиз-контроль,ABS,ESP,Кондиционер,Спальное место,GPS-трекер,Тахограф,Lane Assist',
        'is_featured': True,
        'dimensions_l': 13.5, 'dimensions_w': 2.5, 'dimensions_h': 4.0,
        'max_speed': 130, 'drive_type': '6x4', 'axles': 3
    },
    {
        'name': 'Isuzu Forward FRD 90 Автовышка',
        'model': 'FRD 90',
        'year': 2022,
        'payload': 5.0,
        'body_type': 'Автовышка',
        'volume': 0.0,
        'engine_volume': 7.8,
        'engine_power': 260,
        'fuel_type': 'Дизель',
        'fuel_consumption': 19.0,
        'transmission': 'Механика 6 ст.',
        'color': 'Жёлтый',
        'mileage': 41000,
        'price_per_day': 20000.0,
        'price_with_driver': 26000.0,
        'deposit': 65000.0,
        'image': 'truck10.jpg',
        'description': 'Телескопическая автовышка с рабочей высотой 22 метра для монтажных, отделочных и ремонтных работ на высоте. Люлька с ограждением вмещает двух рабочих и 200 кг груза. Четыре гидравлических аутригера обеспечивают устойчивость на любой поверхности. Поворот люльки 360°.',
        'features': 'Высота 22м,Люлька 200кг,Поворот 360°,4 аутригера,Джойстик управления,ABS,GPS-трекер,Тахограф,Защита от перегрузки',
        'is_featured': False,
        'dimensions_l': 9.5, 'dimensions_w': 2.45, 'dimensions_h': 4.2,
        'max_speed': 95, 'drive_type': '4x2', 'axles': 2
    },
]

def seed_trucks():
    if Truck.query.count() == 0:
        for t in TRUCKS_DATA:
            truck = Truck(**t)
            db.session.add(truck)
        db.session.commit()

def seed_settings():
    defaults = [
        ('insurance_rate', '5', 'Процент страховки от стоимости аренды'),
        ('min_rent_days', '1', 'Минимальный срок аренды (дней)'),
        ('max_rent_days', '90', 'Максимальный срок аренды (дней)'),
        ('working_hours', '8:00 - 20:00', 'Часы работы офиса'),
        ('pickup_address', 'г. Москва, ул. Промышленная, д. 15', 'Адрес выдачи авто'),
    ]
    for key, val, desc in defaults:
        if not SiteSettings.query.filter_by(key=key).first():
            db.session.add(SiteSettings(key=key, value=val, description=desc))
    db.session.commit()

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_login = datetime.utcnow()
        db.session.commit()

@app.context_processor
def inject_globals():
    from config import config as cfg
    c = cfg[os.environ.get('FLASK_ENV', 'default')]
    return dict(
        company_name=c.COMPANY_NAME,
        company_phone=c.COMPANY_PHONE,
        company_address=c.COMPANY_ADDRESS,
        now=datetime.utcnow()
    )

@app.route('/')
def index():
    featured = Truck.query.filter_by(is_featured=True, status='available').limit(4).all()
    total_trucks = Truck.query.count()
    total_clients = User.query.filter_by(is_admin=False).count()
    total_bookings = Booking.query.filter_by(status='completed').count()
    recent_reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(5).all()
    return render_template('index.html', featured=featured,
                           total_trucks=total_trucks,
                           total_clients=total_clients,
                           total_bookings=total_bookings,
                           recent_reviews=recent_reviews)

@app.route('/catalog')
def catalog():
    page = request.args.get('page', 1, type=int)
    body_type = request.args.get('body_type', '')
    min_payload = request.args.get('min_payload', 0, type=float)
    max_payload = request.args.get('max_payload', 999, type=float)
    min_price = request.args.get('min_price', 0, type=float)
    max_price = request.args.get('max_price', 999999, type=float)
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'price_asc')

    query = Truck.query
    if body_type:
        query = query.filter(Truck.body_type == body_type)
    if status:
        query = query.filter(Truck.status == status)
    query = query.filter(Truck.payload >= min_payload, Truck.payload <= max_payload)
    query = query.filter(Truck.price_per_day >= min_price, Truck.price_per_day <= max_price)

    if sort == 'price_asc':
        query = query.order_by(Truck.price_per_day.asc())
    elif sort == 'price_desc':
        query = query.order_by(Truck.price_per_day.desc())
    elif sort == 'payload_desc':
        query = query.order_by(Truck.payload.desc())
    elif sort == 'year_desc':
        query = query.order_by(Truck.year.desc())

    trucks = query.paginate(page=page, per_page=9, error_out=False)
    body_types = db.session.query(Truck.body_type).distinct().all()
    body_types = [bt[0] for bt in body_types]
    return render_template('catalog.html', trucks=trucks, body_types=body_types,
                           current_filters=request.args)

@app.route('/truck/<int:truck_id>')
def truck_detail(truck_id):
    truck = Truck.query.get_or_404(truck_id)
    reviews = Review.query.filter_by(truck_id=truck_id, is_approved=True).order_by(Review.created_at.desc()).all()
    similar = Truck.query.filter(
        Truck.body_type == truck.body_type,
        Truck.id != truck_id
    ).limit(3).all()
    user_can_review = False
    if current_user.is_authenticated:
        completed = Booking.query.filter_by(
            user_id=current_user.id, truck_id=truck_id, status='completed'
        ).first()
        already_reviewed = Review.query.filter_by(user_id=current_user.id, truck_id=truck_id).first()
        user_can_review = completed and not already_reviewed
    return render_template('truck_detail.html', truck=truck, reviews=reviews,
                           similar=similar, user_can_review=user_can_review)

@app.route('/truck/<int:truck_id>/review', methods=['POST'])
@login_required
def add_review(truck_id):
    truck = Truck.query.get_or_404(truck_id)
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    if not rating or rating < 1 or rating > 5:
        flash('Укажите оценку от 1 до 5.', 'danger')
        return redirect(url_for('truck_detail', truck_id=truck_id))
    booking = Booking.query.filter_by(user_id=current_user.id, truck_id=truck_id, status='completed').first()
    if not booking:
        flash('Вы можете оставить отзыв только после завершённой аренды.', 'warning')
        return redirect(url_for('truck_detail', truck_id=truck_id))
    existing = Review.query.filter_by(user_id=current_user.id, truck_id=truck_id).first()
    if existing:
        flash('Вы уже оставили отзыв об этом автомобиле.', 'info')
        return redirect(url_for('truck_detail', truck_id=truck_id))
    review = Review(user_id=current_user.id, truck_id=truck_id,
                    booking_id=booking.id, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    flash('Спасибо за отзыв!', 'success')
    return redirect(url_for('truck_detail', truck_id=truck_id))

@app.route('/booking/<int:truck_id>', methods=['GET', 'POST'])
@login_required
def booking(truck_id):
    truck = Truck.query.get_or_404(truck_id)
    if truck.status != 'available':
        flash('Этот автомобиль сейчас недоступен для аренды.', 'warning')
        return redirect(url_for('truck_detail', truck_id=truck_id))
    if request.method == 'POST':
        start_str = request.form.get('start_date')
        end_str = request.form.get('end_date')
        with_driver = request.form.get('with_driver') == 'on'
        with_insurance = request.form.get('with_insurance') == 'on'
        pickup = request.form.get('pickup_location', '')
        notes = request.form.get('notes', '')

        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Неверный формат дат.', 'danger')
            return redirect(url_for('booking', truck_id=truck_id))

        if start_date < date.today():
            flash('Дата начала не может быть в прошлом.', 'danger')
            return redirect(url_for('booking', truck_id=truck_id))
        if end_date <= start_date:
            flash('Дата окончания должна быть позже даты начала.', 'danger')
            return redirect(url_for('booking', truck_id=truck_id))

        if not truck.is_available_for(start_date, end_date):
            flash('Автомобиль занят на выбранные даты.', 'danger')
            return redirect(url_for('booking', truck_id=truck_id))

        days = (end_date - start_date).days
        base = truck.price_per_day * days
        driver_cost = (truck.price_with_driver - truck.price_per_day) * days if with_driver and truck.price_with_driver else 0
        insurance_cost = base * 0.05 if with_insurance else 0
        total = base + driver_cost + insurance_cost

        b = Booking(
            user_id=current_user.id,
            truck_id=truck_id,
            start_date=start_date,
            end_date=end_date,
            total_days=days,
            base_price=base,
            with_driver=with_driver,
            with_insurance=with_insurance,
            driver_price=driver_cost,
            insurance_price=insurance_cost,
            total_price=total,
            deposit_paid=0,
            pickup_location=pickup,
            notes=notes,
            contract_number=generate_contract_number()
        )
        db.session.add(b)
        db.session.flush()
        create_notification(current_user.id, 'Заявка создана',
                            f'Ваша заявка #{b.contract_number} на аренду {truck.name} принята в обработку.',
                            'success', url_for('profile'))
        db.session.commit()
        flash('Заявка успешно оформлена! Ожидайте подтверждения.', 'success')
        return redirect(url_for('booking_confirm', booking_id=b.id))

    booked_dates = []
    bookings = Booking.query.filter(
        Booking.truck_id == truck_id,
        Booking.status.in_(['confirmed', 'active', 'pending'])
    ).all()
    for b in bookings:
        d = b.start_date
        while d < b.end_date:
            booked_dates.append(d.strftime('%Y-%m-%d'))
            d += timedelta(days=1)

    return render_template('booking.html', truck=truck, booked_dates=booked_dates)

@app.route('/booking/confirm/<int:booking_id>')
@login_required
def booking_confirm(booking_id):
    b = Booking.query.get_or_404(booking_id)
    if b.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('booking_confirm.html', booking=b)

@app.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    b = Booking.query.get_or_404(booking_id)
    if b.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    if b.status in ('completed', 'cancelled'):
        flash('Эту заявку нельзя отменить.', 'warning')
        return redirect(url_for('profile'))
    b.status = 'cancelled'
    create_notification(current_user.id, 'Бронирование отменено',
                        f'Ваша заявка #{b.contract_number} была отменена.', 'warning')
    db.session.commit()
    flash('Бронирование отменено.', 'info')
    return redirect(url_for('profile'))

@app.route('/booking/<int:booking_id>/pdf')
@login_required
def booking_pdf(booking_id):
    b = Booking.query.get_or_404(booking_id)
    if b.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    pdf_bytes = generate_contract_pdf(b)
    return send_file(BytesIO(pdf_bytes), mimetype='application/pdf',
                     download_name=f'contract_{b.contract_number}.pdf')

def generate_contract_pdf(booking):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('title', parent=styles['Title'], fontSize=16, spaceAfter=6)
    normal = styles['Normal']
    normal.fontSize = 11

    story.append(Paragraph('ДОГОВОР АРЕНДЫ ТРАНСПОРТНОГО СРЕДСТВА', title_style))
    story.append(Paragraph(f'№ {booking.contract_number}', styles['Normal']))
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(f'Дата составления: {datetime.utcnow().strftime("%d.%m.%Y")}', normal))
    story.append(Spacer(1, 5*mm))

    data = [
        ['Параметр', 'Значение'],
        ['Арендатор', booking.user.name],
        ['Email арендатора', booking.user.email],
        ['Телефон', booking.user.phone or '—'],
        ['Транспортное средство', booking.truck.name],
        ['Гос. номер / модель', booking.truck.model],
        ['Дата начала аренды', booking.start_date.strftime('%d.%m.%Y')],
        ['Дата окончания аренды', booking.end_date.strftime('%d.%m.%Y')],
        ['Количество дней', str(booking.total_days)],
        ['Базовая стоимость', f'{booking.base_price:,.0f} ₽'],
        ['Водитель', 'Включён' if booking.with_driver else 'Не включён'],
        ['Страховка', 'Включена' if booking.with_insurance else 'Не включена'],
        ['ИТОГО', f'{booking.total_price:,.0f} ₽'],
        ['Статус', booking.status],
    ]

    table = Table(data, colWidths=[80*mm, 90*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0096C7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#CAF0F8')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F0FDFF')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph('Подписи сторон:', styles['Heading2']))
    story.append(Spacer(1, 20*mm))

    sig_data = [
        ['Арендодатель: ___________________', 'Арендатор: ___________________'],
        [app.config['COMPANY_NAME'], booking.user.name],
    ]
    sig_table = Table(sig_data, colWidths=[85*mm, 85*mm])
    story.append(sig_table)

    doc.build(story)
    return buffer.getvalue()

@app.route('/profile')
@login_required
def profile():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
    return render_template('profile.html', bookings=bookings, notifications=notifications)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def profile_edit():
    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name).strip()
        current_user.phone = request.form.get('phone', '').strip()
        current_user.company = request.form.get('company', '').strip()
        current_user.address = request.form.get('address', '').strip()
        current_user.passport_series = request.form.get('passport_series', '').strip()
        current_user.driver_license = request.form.get('driver_license', '').strip()
        new_password = request.form.get('new_password', '').strip()
        if new_password:
            if len(new_password) < 6:
                flash('Пароль должен быть не менее 6 символов.', 'danger')
                return redirect(url_for('profile_edit'))
            current_user.set_password(new_password)
        db.session.commit()
        flash('Профиль обновлён!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile_edit.html')

@app.route('/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/calculate')
def calculate_price():
    truck_id = request.args.get('truck_id', type=int)
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')
    with_driver = request.args.get('with_driver') == 'true'
    with_insurance = request.args.get('with_insurance') == 'true'

    if not all([truck_id, start_str, end_str]):
        return jsonify({'error': 'Missing params'}), 400

    truck = Truck.query.get(truck_id)
    if not truck:
        return jsonify({'error': 'Truck not found'}), 404

    try:
        start = datetime.strptime(start_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date'}), 400

    if end <= start:
        return jsonify({'error': 'Invalid range'}), 400

    days = (end - start).days
    base = truck.price_per_day * days
    driver_cost = (truck.price_with_driver - truck.price_per_day) * days if with_driver and truck.price_with_driver else 0
    insurance_cost = round(base * 0.05, 2) if with_insurance else 0
    total = base + driver_cost + insurance_cost
    available = truck.is_available_for(start, end)

    return jsonify({
        'days': days,
        'base': base,
        'driver': driver_cost,
        'insurance': insurance_cost,
        'total': total,
        'available': available
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            flash(f'Добро пожаловать, {user.name}!', 'success')
            return redirect(next_page or url_for('index'))
        flash('Неверный email или пароль.', 'danger')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not all([name, email, password]):
            flash('Заполните все обязательные поля.', 'danger')
            return redirect(url_for('register'))
        if password != confirm:
            flash('Пароли не совпадают.', 'danger')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Пароль должен быть не менее 6 символов.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Этот email уже зарегистрирован.', 'danger')
            return redirect(url_for('register'))

        admin_email = app.config.get('ADMIN_EMAIL', '')
        is_admin = (email == admin_email.lower())

        user = User(name=name, email=email, phone=phone, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        create_notification(user.id, 'Добро пожаловать!',
                            f'Рады видеть вас, {name}! Начните с просмотра нашего каталога грузовиков.', 'success')
        db.session.commit()
        login_user(user)
        flash(f'Регистрация прошла успешно! Добро пожаловать, {name}!', 'success')
        return redirect(url_for('index'))
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    stats = {
        'total_trucks': Truck.query.count(),
        'available_trucks': Truck.query.filter_by(status='available').count(),
        'total_users': User.query.filter_by(is_admin=False).count(),
        'total_bookings': Booking.query.count(),
        'pending_bookings': Booking.query.filter_by(status='pending').count(),
        'active_bookings': Booking.query.filter_by(status='active').count(),
        'completed_bookings': Booking.query.filter_by(status='completed').count(),
        'total_revenue': db.session.query(func.sum(Booking.total_price)).filter_by(status='completed').scalar() or 0,
        'month_revenue': db.session.query(func.sum(Booking.total_price)).filter(
            Booking.status == 'completed',
            extract('month', Booking.created_at) == datetime.utcnow().month,
            extract('year', Booking.created_at) == datetime.utcnow().year
        ).scalar() or 0,
    }
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    monthly_data = []
    for i in range(6):
        m = (datetime.utcnow().month - i - 1) % 12 + 1
        y = datetime.utcnow().year if datetime.utcnow().month - i > 0 else datetime.utcnow().year - 1
        rev = db.session.query(func.sum(Booking.total_price)).filter(
            Booking.status == 'completed',
            extract('month', Booking.created_at) == m,
            extract('year', Booking.created_at) == y
        ).scalar() or 0
        count = Booking.query.filter(
            extract('month', Booking.created_at) == m,
            extract('year', Booking.created_at) == y
        ).count()
        monthly_data.insert(0, {'month': f'{m:02d}/{y}', 'revenue': float(rev), 'count': count})

    return render_template('admin/dashboard.html', stats=stats,
                           recent_bookings=recent_bookings,
                           recent_users=recent_users,
                           monthly_data=monthly_data)

@app.route('/admin/trucks')
@login_required
@admin_required
def admin_trucks():
    trucks = Truck.query.order_by(Truck.created_at.desc()).all()
    return render_template('admin/trucks.html', trucks=trucks)

@app.route('/admin/trucks/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_truck_add():
    if request.method == 'POST':
        t = Truck(
            name=request.form['name'],
            model=request.form['model'],
            year=int(request.form['year']),
            payload=float(request.form['payload']),
            body_type=request.form['body_type'],
            volume=float(request.form.get('volume') or 0),
            engine_volume=float(request.form.get('engine_volume') or 0),
            engine_power=int(request.form.get('engine_power') or 0),
            fuel_type=request.form.get('fuel_type', 'Дизель'),
            fuel_consumption=float(request.form.get('fuel_consumption') or 0),
            transmission=request.form.get('transmission', ''),
            color=request.form.get('color', ''),
            mileage=int(request.form.get('mileage') or 0),
            price_per_day=float(request.form['price_per_day']),
            price_with_driver=float(request.form.get('price_with_driver') or 0) or None,
            deposit=float(request.form.get('deposit') or 0),
            description=request.form.get('description', ''),
            features=request.form.get('features', ''),
            status=request.form.get('status', 'available'),
            is_featured=request.form.get('is_featured') == 'on',
            dimensions_l=float(request.form.get('dimensions_l') or 0) or None,
            dimensions_w=float(request.form.get('dimensions_w') or 0) or None,
            dimensions_h=float(request.form.get('dimensions_h') or 0) or None,
            max_speed=int(request.form.get('max_speed') or 0) or None,
            drive_type=request.form.get('drive_type', '4x2'),
            axles=int(request.form.get('axles') or 2),
            image=request.form.get('image', 'truck_default.jpg'),
        )
        db.session.add(t)
        db.session.commit()
        flash('Грузовик добавлен!', 'success')
        return redirect(url_for('admin_trucks'))
    return render_template('admin/truck_form.html', truck=None, action='add')

@app.route('/admin/trucks/<int:truck_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_truck_edit(truck_id):
    truck = Truck.query.get_or_404(truck_id)
    if request.method == 'POST':
        truck.name = request.form['name']
        truck.model = request.form['model']
        truck.year = int(request.form['year'])
        truck.payload = float(request.form['payload'])
        truck.body_type = request.form['body_type']
        truck.volume = float(request.form.get('volume') or 0)
        truck.engine_volume = float(request.form.get('engine_volume') or 0)
        truck.engine_power = int(request.form.get('engine_power') or 0)
        truck.fuel_type = request.form.get('fuel_type', 'Дизель')
        truck.fuel_consumption = float(request.form.get('fuel_consumption') or 0)
        truck.transmission = request.form.get('transmission', '')
        truck.color = request.form.get('color', '')
        truck.mileage = int(request.form.get('mileage') or 0)
        truck.price_per_day = float(request.form['price_per_day'])
        truck.price_with_driver = float(request.form.get('price_with_driver') or 0) or None
        truck.deposit = float(request.form.get('deposit') or 0)
        truck.description = request.form.get('description', '')
        truck.features = request.form.get('features', '')
        truck.status = request.form.get('status', 'available')
        truck.is_featured = request.form.get('is_featured') == 'on'
        truck.dimensions_l = float(request.form.get('dimensions_l') or 0) or None
        truck.dimensions_w = float(request.form.get('dimensions_w') or 0) or None
        truck.dimensions_h = float(request.form.get('dimensions_h') or 0) or None
        truck.max_speed = int(request.form.get('max_speed') or 0) or None
        truck.drive_type = request.form.get('drive_type', '4x2')
        truck.axles = int(request.form.get('axles') or 2)
        truck.image = request.form.get('image', truck.image)
        db.session.commit()
        flash('Данные грузовика обновлены!', 'success')
        return redirect(url_for('admin_trucks'))
    return render_template('admin/truck_form.html', truck=truck, action='edit')

@app.route('/admin/trucks/<int:truck_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_truck_delete(truck_id):
    truck = Truck.query.get_or_404(truck_id)
    if truck.bookings.count() > 0:
        flash('Нельзя удалить грузовик с историей бронирований.', 'danger')
        return redirect(url_for('admin_trucks'))
    db.session.delete(truck)
    db.session.commit()
    flash('Грузовик удалён.', 'success')
    return redirect(url_for('admin_trucks'))

@app.route('/admin/trucks/<int:truck_id>/status', methods=['POST'])
@login_required
@admin_required
def admin_truck_status(truck_id):
    truck = Truck.query.get_or_404(truck_id)
    new_status = request.form.get('status')
    if new_status in ('available', 'rented', 'maintenance', 'inactive'):
        truck.status = new_status
        db.session.commit()
    return redirect(url_for('admin_trucks'))

@app.route('/admin/bookings')
@login_required
@admin_required
def admin_bookings():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    query = Booking.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    bookings = query.order_by(Booking.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/bookings.html', bookings=bookings, status_filter=status_filter)

@app.route('/admin/bookings/<int:booking_id>/status', methods=['POST'])
@login_required
@admin_required
def admin_booking_status(booking_id):
    b = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '')
    valid = ('pending', 'confirmed', 'active', 'completed', 'cancelled', 'rejected')
    if new_status in valid:
        b.status = new_status
        if admin_notes:
            b.admin_notes = admin_notes
        status_labels = {
            'confirmed': 'подтверждено',
            'active': 'активна',
            'completed': 'завершено',
            'cancelled': 'отменено',
            'rejected': 'отклонено'
        }
        label = status_labels.get(new_status, new_status)
        create_notification(b.user_id, 'Статус бронирования изменён',
                            f'Ваше бронирование #{b.contract_number} — {label}.',
                            'info', url_for('profile'))
        db.session.commit()
        flash('Статус обновлён.', 'success')
    return redirect(url_for('admin_bookings'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = User.query
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%'))
        )
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/users.html', users=users, search=search)

@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_user_toggle(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Нельзя заблокировать самого себя.', 'danger')
        return redirect(url_for('admin_users'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'активирован' if user.is_active else 'заблокирован'
    flash(f'Пользователь {user.name} {status}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/promote', methods=['POST'])
@login_required
@admin_required
def admin_user_promote(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    role = 'администратором' if user.is_admin else 'обычным пользователем'
    flash(f'{user.name} теперь {role}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/reviews')
@login_required
@admin_required
def admin_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)

@app.route('/admin/reviews/<int:review_id>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_review_toggle(review_id):
    r = Review.query.get_or_404(review_id)
    r.is_approved = not r.is_approved
    db.session.commit()
    flash('Статус отзыва изменён.', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_review_delete(review_id):
    r = Review.query.get_or_404(review_id)
    db.session.delete(r)
    db.session.commit()
    flash('Отзыв удалён.', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    year = request.args.get('year', datetime.utcnow().year, type=int)
    monthly = []
    for m in range(1, 13):
        rev = db.session.query(func.sum(Booking.total_price)).filter(
            Booking.status == 'completed',
            extract('month', Booking.created_at) == m,
            extract('year', Booking.created_at) == year
        ).scalar() or 0
        cnt = Booking.query.filter(
            extract('month', Booking.created_at) == m,
            extract('year', Booking.created_at) == year
        ).count()
        monthly.append({'month': m, 'revenue': float(rev), 'bookings': cnt})

    top_trucks = db.session.query(
        Truck, func.count(Booking.id).label('cnt'),
        func.sum(Booking.total_price).label('revenue')
    ).join(Booking).filter(Booking.status == 'completed').group_by(Truck.id).order_by(func.count(Booking.id).desc()).limit(5).all()

    return render_template('admin/reports.html', monthly=monthly, top_trucks=top_trucks, year=year)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_settings():
    if request.method == 'POST':
        for key in request.form:
            setting = SiteSettings.query.filter_by(key=key).first()
            if setting:
                setting.value = request.form[key]
        db.session.commit()
        flash('Настройки сохранены.', 'success')
        return redirect(url_for('admin_settings'))
    settings = SiteSettings.query.all()
    return render_template('admin/settings.html', settings=settings)

@app.route('/admin/notify', methods=['POST'])
@login_required
@admin_required
def admin_notify_all():
    title = request.form.get('title', '')
    message = request.form.get('message', '')
    if title and message:
        users = User.query.filter_by(is_admin=False, is_active=True).all()
        for u in users:
            create_notification(u.id, title, message, 'info')
        db.session.commit()
        flash(f'Уведомление отправлено {len(users)} пользователям.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

with app.app_context():
    db.create_all()
    seed_trucks()
    seed_settings()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
