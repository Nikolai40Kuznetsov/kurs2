import sys
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QTabWidget, 
                             QMessageBox, QSpinBox, QHeaderView, QGroupBox,
                             QTextEdit, QComboBox, QListWidget, QListWidgetItem,
                             QDialog, QDialogButtonBox, QFormLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime

# Создаем базу данных SQLite
engine = create_engine('sqlite:///online_store.db', echo=False)
Base = declarative_base()

# Определяем модели данных
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), default='user')  # 'user', 'seller' или 'admin'
    pickup_point_id = Column(Integer, ForeignKey('pickup_points.id', ondelete='SET NULL'), nullable=True)
    
    carts = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    pickup_point = relationship("PickupPoint", back_populates="sellers")
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

class Cart(Base):
    __tablename__ = 'carts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(100), nullable=False)
    product_price = Column(Float, nullable=False)
    product_stock = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    
    user = relationship("User", back_populates="carts")
    
    def __repr__(self):
        return f"<Cart(user_id={self.user_id}, product_id={self.product_id}, quantity={self.quantity})>"

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user_name = Column(String(50), nullable=False)
    order_date = Column(DateTime, default=datetime.now)
    total = Column(Float, nullable=False)
    recipient_name = Column(String(100), nullable=False)
    address = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    delivery_method = Column(String(50), nullable=False)
    pickup_point_id = Column(Integer, ForeignKey('pickup_points.id', ondelete='SET NULL'), nullable=True)
    items = Column(JSON, nullable=False)  # Хранит список товаров в формате JSON
    
    user = relationship("User", back_populates="orders")
    pickup_point = relationship("PickupPoint", back_populates="orders")
    
    def __repr__(self):
        return f"<Order(user_id={self.user_id}, total={self.total}, date={self.order_date})>"

class PickupPoint(Base):
    __tablename__ = 'pickup_points'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(200), nullable=False)
    working_hours = Column(String(100), nullable=False)
    
    sellers = relationship("User", back_populates="pickup_point")
    orders = relationship("Order", back_populates="pickup_point")
    
    def __repr__(self):
        return f"<PickupPoint(name='{self.name}', address='{self.address}')>"

# Создаем таблицы в базе данных
Base.metadata.create_all(engine)

# Создаем сессию для работы с БД
Session = sessionmaker(bind=engine)

class UserManager:
    # Класс для управления пользователями через БД
    def __init__(self):
        self.session = Session()
        self.ensure_default_users()
        self.ensure_default_pickup_points()
    
    def ensure_default_users(self):
        # Создает тестовых пользователей если их нет
        if self.session.query(User).count() == 0:
            default_users = [
                ("user1", "pass123", "user", None),
                ("user2", "qwerty", "user", None),
                ("admin", "admin123", "admin", None),
            ]
            for username, password, role, pickup_point_id in default_users:
                user = User(username=username, password=password, role=role, pickup_point_id=pickup_point_id)
                self.session.add(user)
            self.session.commit()
    
    def ensure_default_pickup_points(self):
        # Создает тестовые пункты выдачи если их нет
        if self.session.query(PickupPoint).count() == 0:
            default_points = [
                ("Пункт выдачи №1 (Центральный)", "ул. Ленина, 15", "Пн-Пт: 9:00-20:00, Сб: 10:00-18:00"),
                ("Пункт выдачи №2 (Западный)", "пр. Победителей, 23", "Пн-Пт: 10:00-21:00, Сб-Вс: 10:00-19:00"),
                ("Пункт выдачи №3 (Восточный)", "ул. Советская, 8", "Пн-Вс: 9:00-22:00"),
            ]
            for name, address, hours in default_points:
                point = PickupPoint(name=name, address=address, working_hours=hours)
                self.session.add(point)
            self.session.commit()
            
            # Привязываем продавцов к пунктам выдачи
            sellers = self.session.query(User).filter_by(role='seller').all()
            points = self.session.query(PickupPoint).all()
            if sellers and points:
                for i, seller in enumerate(sellers):
                    seller.pickup_point_id = points[i % len(points)].id
                self.session.commit()
    
    def check_credentials(self, username, password):
        # Проверяет логин и пароль, возвращает роль пользователя
        user = self.session.query(User).filter_by(username=username, password=password).first()
        if user:
            return user.role
        return None
    
    def get_user_role(self, username):
        user = self.session.query(User).filter_by(username=username).first()
        return user.role if user else None
    
    def add_user(self, username, password, role='user', pickup_point_id=None):
        # Добавляет нового пользователя
        try:
            # Проверяем, существует ли пользователь
            existing_user = self.session.query(User).filter_by(username=username).first()
            if existing_user:
                return False
            
            user = User(username=username, password=password, role=role, pickup_point_id=pickup_point_id)
            self.session.add(user)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при добавлении пользователя: {e}")
            return False
    
    def get_user_id(self, username):
        # Получает ID пользователя по имени
        user = self.session.query(User).filter_by(username=username).first()
        return user.id if user else None
    
    def get_user_by_id(self, user_id):
        return self.session.query(User).filter_by(id=user_id).first()
    
    def get_all_users(self):
        """Возвращает список всех пользователей"""
        return self.session.query(User).all()
    
    def get_all_sellers(self):
        """Возвращает список всех продавцов"""
        return self.session.query(User).filter_by(role='seller').all()
    
    def update_seller_pickup_point(self, seller_id, pickup_point_id):
        """Обновляет пункт выдачи продавца"""
        try:
            seller = self.session.query(User).filter_by(id=seller_id).first()
            if seller and seller.role == 'seller':
                seller.pickup_point_id = pickup_point_id
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при обновлении пункта выдачи продавца: {e}")
            return False
    
    def delete_seller(self, seller_id):
        """Удаляет продавца"""
        try:
            seller = self.session.query(User).filter_by(id=seller_id, role='seller').first()
            if not seller:
                return False, "Продавец не найден"
            
            # Проверяем, есть ли у продавца заказы
            orders_count = self.session.query(Order).filter_by(user_id=seller_id).count()
            if orders_count > 0:
                return False, f"У продавца есть {orders_count} заказ(ов). Сначала удалите заказы."
            
            # Удаляем корзину продавца (если есть)
            self.session.query(Cart).filter_by(user_id=seller_id).delete()
            
            # Удаляем продавца
            self.session.delete(seller)
            self.session.commit()
            return True, "Продавец удален"
        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при удалении продавца: {e}")
            return False, str(e)
    
    def get_all_pickup_points(self):
        """Возвращает список всех пунктов выдачи"""
        return self.session.query(PickupPoint).all()
    
    def add_pickup_point(self, name, address, working_hours):
        """Добавляет новый пункт выдачи"""
        try:
            point = PickupPoint(name=name, address=address, working_hours=working_hours)
            self.session.add(point)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при добавлении пункта выдачи: {e}")
            return False
    
    def delete_pickup_point(self, point_id):
        """Удаляет пункт выдачи"""
        try:
            point = self.session.query(PickupPoint).filter_by(id=point_id).first()
            if not point:
                return False, "Пункт выдачи не найден"
            
            # Проверяем, есть ли привязанные продавцы
            sellers = self.session.query(User).filter_by(pickup_point_id=point_id).all()
            if sellers:
                # Отвязываем продавцов от пункта выдачи
                for seller in sellers:
                    seller.pickup_point_id = None
                self.session.commit()
            
            # Проверяем, есть ли заказы с этим пунктом выдачи
            orders = self.session.query(Order).filter_by(pickup_point_id=point_id).all()
            if orders:
                # Отвязываем заказы от пункта выдачи
                for order in orders:
                    order.pickup_point_id = None
                self.session.commit()
            
            # Удаляем пункт выдачи
            self.session.delete(point)
            self.session.commit()
            return True, "Пункт выдачи удален"
        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при удалении пункта выдачи: {e}")
            return False, str(e)
    
    def close(self):
        """Закрывает сессию"""
        self.session.close()

class CartManager:
    """Класс для управления корзиной через БД"""
    def __init__(self, username):
        self.session = Session()
        self.user_manager = UserManager()
        self.user_id = self.user_manager.get_user_id(username)
        if self.user_manager:
            self.user_manager.close()
    
    def save_cart(self, cart):
        """Сохраняет корзину в БД"""
        try:
            # Удаляем старые записи корзины для этого пользователя
            self.session.query(Cart).filter_by(user_id=self.user_id).delete()
            
            # Добавляем новые записи
            for product_id, item_data in cart.items():
                product = item_data["product"]
                cart_item = Cart(
                    user_id=self.user_id,
                    product_id=product_id,
                    product_name=product["name"],
                    product_price=product["price"],
                    product_stock=product["stock"],
                    quantity=item_data["quantity"]
                )
                self.session.add(cart_item)
            
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при сохранении корзины: {e}")
            return False
    
    def load_cart(self):
        """Загружает корзину из БД"""
        try:
            cart_items = self.session.query(Cart).filter_by(user_id=self.user_id).all()
            
            cart = {}
            for item in cart_items:
                product = {
                    "id": item.product_id,
                    "name": item.product_name,
                    "price": item.product_price,
                    "stock": item.product_stock
                }
                cart[item.product_id] = {
                    "product": product,
                    "quantity": item.quantity
                }
            return cart
        except Exception as e:
            print(f"Ошибка при загрузке корзины: {e}")
            return {}
    
    def clear_cart(self):
        """Очищает корзину пользователя в БД"""
        try:
            self.session.query(Cart).filter_by(user_id=self.user_id).delete()
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при очистке корзины: {e}")
            return False
    
    def close(self):
        """Закрывает сессию"""
        self.session.close()

class OrderManager:
    """Класс для управления заказами"""
    def __init__(self):
        self.session = Session()
    
    def save_order(self, user_id, user_name, items, total, recipient_name, address, phone, delivery_method, pickup_point_id=None):
        """Сохраняет заказ в БД"""
        try:
            order = Order(
                user_id=user_id,
                user_name=user_name,
                total=total,
                recipient_name=recipient_name,
                address=address,
                phone=phone,
                delivery_method=delivery_method,
                pickup_point_id=pickup_point_id,
                items=items
            )
            self.session.add(order)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при сохранении заказа: {e}")
            return False
    
    def get_all_orders(self):
        """Получает все заказы"""
        try:
            return self.session.query(Order).order_by(Order.order_date.desc()).all()
        except Exception as e:
            print(f"Ошибка при получении заказов: {e}")
            return []
    
    def close(self):
        """Закрывает сессию"""
        self.session.close()

class ProductManager:
    """Класс для управления товарами"""
    def __init__(self):
        # Используем список товаров, хранящийся в памяти
        # В реальном приложении здесь могла бы быть таблица в БД
        self.products = [
            {"id": 1, "name": "Ноутбук", "price": 45000, "stock": 10},
            {"id": 2, "name": "Смартфон", "price": 25000, "stock": 15},
            {"id": 3, "name": "Наушники", "price": 3000, "stock": 30},
            {"id": 4, "name": "Мышь", "price": 1500, "stock": 25},
            {"id": 5, "name": "Клавиатура", "price": 3500, "stock": 20},
            {"id": 6, "name": "Монитор", "price": 18000, "stock": 8},
        ]
        self.next_id = 7
    
    def get_all_products(self):
        return self.products
    
    def add_product(self, name, price, stock):
        """Добавляет новый товар"""
        try:
            product = {
                "id": self.next_id,
                "name": name,
                "price": price,
                "stock": stock
            }
            self.products.append(product)
            self.next_id += 1
            return True
        except Exception as e:
            print(f"Ошибка при добавлении товара: {e}")
            return False
    
    def update_product(self, product_id, name=None, price=None, stock=None):
        """Обновляет товар"""
        try:
            for product in self.products:
                if product["id"] == product_id:
                    if name is not None:
                        product["name"] = name
                    if price is not None:
                        product["price"] = price
                    if stock is not None:
                        product["stock"] = stock
                    return True
            return False
        except Exception as e:
            print(f"Ошибка при обновлении товара: {e}")
            return False
    
    def delete_product(self, product_id):
        """Удаляет товар"""
        try:
            for i, product in enumerate(self.products):
                if product["id"] == product_id:
                    del self.products[i]
                    return True
            return False
        except Exception as e:
            print(f"Ошибка при удалении товара: {e}")
            return False
    
    def get_product_by_id(self, product_id):
        for product in self.products:
            if product["id"] == product_id:
                return product
        return None

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_manager = UserManager()
        self.setWindowTitle("Авторизация - Интернет-магазин")
        self.setFixedSize(500, 400) 

        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4A90E2, stop:0.5 #9B59B6, stop:1 #1ABC9C);
            }
            QLabel {
                color: black;
            }
            QLineEdit {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Добро пожаловать в интернет-магазин")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")
        self.login_input.setFixedWidth(300)  
        layout.addWidget(self.login_input, alignment=Qt.AlignCenter)
        
        layout.addSpacing(10)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(300)  
        layout.addWidget(self.password_input, alignment=Qt.AlignCenter)
        
        layout.addSpacing(20)
        
        login_btn = QPushButton("Войти")
        login_btn.setFixedWidth(200)  
        login_btn.clicked.connect(self.check_login)
        layout.addWidget(login_btn, alignment=Qt.AlignCenter)
        
        layout.addSpacing(10)
        
        register_btn = QPushButton("Регистрация")
        register_btn.setFixedWidth(200)
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #1ABC9C;
            }
            QPushButton:hover {
                background-color: #16A085;
            }
        """)
        register_btn.clicked.connect(self.show_registration)
        layout.addWidget(register_btn, alignment=Qt.AlignCenter)
        
        self.info_label = QLabel("Тестовые пользователи: user1/pass123, user2/qwerty\nПродавцы: создаются админом\nАдмин: admin/admin123")
        self.info_label.setStyleSheet("color: #ecf0f1; font-size: 10px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
    
    def check_login(self):
        login = self.login_input.text().strip()
        password = self.password_input.text()
        
        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите логин и пароль")
            return
        
        role = self.user_manager.check_credentials(login, password)
        if role:
            self.main_app = MainApplication(login, role)
            self.main_app.show()
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
    
    def show_registration(self):
        self.reg_window = RegistrationWindow(self.user_manager)
        self.reg_window.show()
    
    def closeEvent(self, event):
        """Закрываем соединение с БД при закрытии окна"""
        self.user_manager.close()
        event.accept()

class RegistrationWindow(QMainWindow):
    def __init__(self, user_manager):
        super().__init__()
        self.user_manager = user_manager
        self.setWindowTitle("Регистрация - Интернет-магазин")
        self.setFixedSize(500, 400)
        
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4A90E2, stop:0.5 #9B59B6, stop:1 #1ABC9C);
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Регистрация нового пользователя")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Придумайте логин")
        self.login_input.setFixedWidth(250)
        layout.addWidget(self.login_input, alignment=Qt.AlignCenter)
        
        layout.addSpacing(10)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Придумайте пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(250)
        layout.addWidget(self.password_input, alignment=Qt.AlignCenter)
        
        layout.addSpacing(10)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Подтвердите пароль")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setFixedWidth(250)
        layout.addWidget(self.confirm_password_input, alignment=Qt.AlignCenter)
        
        layout.addSpacing(20)
        
        register_btn = QPushButton("Зарегистрироваться")
        register_btn.setFixedWidth(200)
        register_btn.clicked.connect(self.register)
        layout.addWidget(register_btn, alignment=Qt.AlignCenter)
    
    def register(self):
        login = self.login_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_password_input.text()
        
        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
        
        if len(password) < 4:
            QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 4 символа")
            return
        
        if self.user_manager.add_user(login, password):
            QMessageBox.information(self, "Успешно", f"Пользователь {login} успешно зарегистрирован!")
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует или произошла ошибка")

class MainApplication(QMainWindow):
    def __init__(self, username, role):
        super().__init__()
        self.username = username
        self.role = role
        self.cart_manager = CartManager(username)
        self.order_manager = OrderManager()
        self.product_manager = ProductManager()
        self.setWindowTitle(f"Интернет-магазин - Пользователь: {username} ({role})")
        self.setGeometry(100, 100, 1200, 700)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f8ff;
            }
            QTabWidget::pane {
                border: 2px solid #9B59B6;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #9B59B6;
            }
            QTabBar::tab:hover {
                background-color: #1ABC9C;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f0f0f0;
                gridline-color: #3498db;
            }
            QHeaderView::section {
                background-color: #9B59B6;
                color: white;
                padding: 5px;
                border: 1px solid #8E44AD;
            }
            QPushButton {
                background-color: #1ABC9C;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16A085;
            }
            QGroupBox {
                border: 2px solid #9B59B6;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #9B59B6;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #9B59B6;
            }
            QSpinBox {
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                color: black;
                background-color: white;
                selection-background-color: #9B59B6;
                selection-color: white;
            }
            QComboBox {
                color: black;
            }
        """)
        
        self.products = self.product_manager.get_all_products()
        
        # Загружаем корзину пользователя из БД (только для обычных пользователей)
        if self.role == 'user':
            self.cart = self.cart_manager.load_cart()
        else:
            self.cart = {}
        
        # Создаем главный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Верхняя панель с кнопкой выхода
        top_panel = QHBoxLayout()
        
        # Заголовок слева
        title_label = QLabel(f"Добро пожаловать, {username}!")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #9B59B6;")
        top_panel.addWidget(title_label)
        
        # Растягиваем пространство
        top_panel.addStretch()
        
        # Кнопка выхода справа
        logout_btn = QPushButton("Выход")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                font-size: 12px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        top_panel.addWidget(logout_btn)
        
        main_layout.addLayout(top_panel)
        
        # Вкладки
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Вкладка с товарами доступна всем
        self.products_tab = ProductsTab(self.products, self.add_to_cart, self.role)
        self.tabs.addTab(self.products_tab, "Товары")
        
        if self.role == 'user':
            # Для обычных пользователей - корзина и доставка
            self.cart_tab = CartTab(self.cart, self.update_cart_quantities, self.remove_from_cart)
            self.delivery_tab = DeliveryTab(self.get_cart_summary, self.clear_cart_after_order, self.username, self.role)
            self.tabs.addTab(self.cart_tab, "Корзина")
            self.tabs.addTab(self.delivery_tab, "Доставка")
            self.tabs.currentChanged.connect(self.on_tab_changed)
        elif self.role == 'seller':
            # Для продавцов - просмотр заказов и управление товарами
            self.orders_tab = OrdersTab()
            self.tabs.addTab(self.orders_tab, "Все заказы")
            self.products_management_tab = ProductsManagementTab(self.product_manager, self.role)
            self.tabs.addTab(self.products_management_tab, "Управление товарами")
        elif self.role == 'admin':
            # Для админа - управление продавцами, пунктами выдачи и товарами
            self.admin_tab = AdminTab()
            self.tabs.addTab(self.admin_tab, "Управление продавцами")
            self.pickup_tab = PickupPointsTab()
            self.tabs.addTab(self.pickup_tab, "Управление пунктами выдачи")
            self.products_management_tab = ProductsManagementTab(self.product_manager, self.role)
            self.tabs.addTab(self.products_management_tab, "Управление товарами")
    
    def logout(self):
        """Выход из аккаунта"""
        # Сохраняем корзину перед выходом
        if self.role == 'user':
            self.cart_manager.save_cart(self.cart)
        self.cart_manager.close()
        self.order_manager.close()
        self.close()
        
        # Показываем окно авторизации
        self.login_window = LoginWindow()
        self.login_window.show()
    
    def closeEvent(self, event):
        """Сохраняем корзину в БД при закрытии программы"""
        if self.role == 'user':
            self.cart_manager.save_cart(self.cart)
        self.cart_manager.close()
        self.order_manager.close()
        event.accept()
    
    def add_to_cart(self, product_id, quantity):
        if self.role != 'user':
            QMessageBox.warning(self, "Доступ запрещен", "Только покупатели могут добавлять товары в корзину")
            return
        product = next((p for p in self.products if p["id"] == product_id), None)
        if product:
            if product_id in self.cart:
                self.cart[product_id]["quantity"] += quantity
            else:
                self.cart[product_id] = {
                    "product": product,
                    "quantity": quantity
                }
            QMessageBox.information(self, "Успешно", f"Товар добавлен в корзину!")
            self.update_cart_display()
    
    def update_cart_quantities(self, product_id, new_quantity):
        if product_id in self.cart:
            if new_quantity > 0:
                self.cart[product_id]["quantity"] = new_quantity
            else:
                del self.cart[product_id]
            self.update_cart_display()
    
    def remove_from_cart(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]
            self.update_cart_display()
    
    def update_cart_display(self):
        if hasattr(self, 'cart_tab'):
            self.cart_tab.update_cart_table()
        if hasattr(self, 'delivery_tab'):
            self.delivery_tab.update_summary()
    
    def get_cart_summary(self):
        items = []
        total = 0
        for item_id, item_data in self.cart.items():
            product = item_data["product"]
            quantity = item_data["quantity"]
            subtotal = product["price"] * quantity
            items.append({
                "name": product["name"],
                "quantity": quantity,
                "price": product["price"],
                "subtotal": subtotal
            })
            total += subtotal
        return items, total
    
    def clear_cart_after_order(self):
        """Очищает корзину после оформления заказа"""
        self.cart.clear()
        self.cart_manager.clear_cart()
        self.update_cart_display()
    
    def on_tab_changed(self, index):
        if index == 1 and hasattr(self, 'cart_tab'):  # Вкладка корзины
            self.cart_tab.update_cart_table()
        elif index == 2 and hasattr(self, 'delivery_tab'):  # Вкладка доставки
            self.delivery_tab.update_summary()

class ProductsTab(QWidget):
    def __init__(self, products, add_to_cart_callback, role):
        super().__init__()
        self.products = products
        self.add_to_cart_callback = add_to_cart_callback
        self.role = role
        layout = QVBoxLayout()
        
        title = QLabel("Каталог товаров")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #9B59B6;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Цена (руб)", "В наличии", "Количество"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)  
        self.update_products_table()
        layout.addWidget(self.table)
        
        add_btn = QPushButton("Добавить выбранный товар в корзину")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #1ABC9C;
                font-size: 12px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #16A085;
            }
        """)
        add_btn.clicked.connect(self.add_selected_to_cart)
        layout.addWidget(add_btn)
        
        if self.role != 'user':
            add_btn.setEnabled(False)
            add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    font-size: 12px;
                    padding: 10px;
                }
            """)
        
        self.setLayout(layout)
    
    def update_products_table(self):
        self.table.setRowCount(len(self.products))
        for row, product in enumerate(self.products):
            self.table.setItem(row, 0, QTableWidgetItem(str(product["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(product["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(product["price"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(product["stock"])))
            spinbox = QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(product["stock"])
            spinbox.setValue(1)
            spinbox.setStyleSheet("""
                QSpinBox {
                    border: 2px solid #3498db;
                    border-radius: 5px;
                    padding: 3px;
                }
            """)
            self.table.setCellWidget(row, 4, spinbox)
    
    def add_selected_to_cart(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            product_id = int(self.table.item(current_row, 0).text())
            spinbox = self.table.cellWidget(current_row, 4)
            quantity = spinbox.value()
            self.add_to_cart_callback(product_id, quantity)
        else:
            QMessageBox.warning(self, "Внимание", "Выберите товар для добавления в корзину")

class CartTab(QWidget):
    def __init__(self, cart, update_callback, remove_callback):
        super().__init__()
        self.cart = cart
        self.update_callback = update_callback
        self.remove_callback = remove_callback
        layout = QVBoxLayout()
        
        title = QLabel("Корзина")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #9B59B6;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Название", "Цена (руб)", "Количество", "Сумма (руб)", "Действия"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        self.total_label = QLabel("Итого: 0 руб.")
        self.total_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_label.setStyleSheet("color: #1ABC9C;")
        self.total_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.total_label)
        
        clear_btn = QPushButton("Очистить корзину")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        clear_btn.clicked.connect(self.clear_cart)
        layout.addWidget(clear_btn)
        
        self.setLayout(layout)
    
    def update_cart_table(self):
        self.table.setRowCount(len(self.cart))
        total = 0
        for row, (item_id, item_data) in enumerate(self.cart.items()):
            product = item_data["product"]
            quantity = item_data["quantity"]
            subtotal = product["price"] * quantity
            total += subtotal
            
            self.table.setItem(row, 0, QTableWidgetItem(product["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(product["price"])))
            
            spinbox = QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(product["stock"])
            spinbox.setValue(quantity)
            spinbox.valueChanged.connect(lambda v, pid=item_id: self.update_callback(pid, v))
            self.table.setCellWidget(row, 2, spinbox)
            
            self.table.setItem(row, 3, QTableWidgetItem(str(subtotal)))
            
            remove_btn = QPushButton("Удалить")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E74C3C;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #C0392B;
                }
            """)
            remove_btn.clicked.connect(lambda checked, pid=item_id: self.remove_callback(pid))
            self.table.setCellWidget(row, 4, remove_btn)
        
        self.total_label.setText(f"Итого: {total} руб.")
    
    def clear_cart(self):
        self.cart.clear()
        self.update_cart_table()
        QMessageBox.information(self, "Успешно", "Корзина очищена")

class DeliveryTab(QWidget):
    def __init__(self, get_cart_summary_callback, clear_cart_callback, username, role):
        super().__init__()
        self.get_cart_summary_callback = get_cart_summary_callback
        self.clear_cart_callback = clear_cart_callback
        self.username = username
        self.role = role
        self.user_manager = UserManager()
        self.pickup_points = self.user_manager.get_all_pickup_points()
        self.user_manager.close()
        
        layout = QVBoxLayout()
        
        title = QLabel("Оформление доставки")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #9B59B6;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        order_group = QGroupBox("Информация о заказе")
        order_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #9B59B6;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        order_layout = QVBoxLayout()
        self.order_text = QTextEdit()
        self.order_text.setReadOnly(True)
        self.order_text.setMaximumHeight(200)
        self.order_text.setStyleSheet("border: 2px solid #3498db; border-radius: 5px; padding: 5px;")
        order_layout.addWidget(self.order_text)
        order_group.setLayout(order_layout)
        layout.addWidget(order_group)
        
        delivery_group = QGroupBox("Информация о доставке")
        delivery_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #9B59B6;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        delivery_layout = QVBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("ФИО получателя")
        self.name_input.setMinimumHeight(35)
        delivery_layout.addWidget(self.name_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Телефон")
        self.phone_input.setMinimumHeight(35)
        delivery_layout.addWidget(self.phone_input)
        
        delivery_method_label = QLabel("Способ доставки:")
        delivery_method_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        delivery_layout.addWidget(delivery_method_label)
        
        self.delivery_method = QComboBox()
        self.delivery_method.addItems(["Курьером", "Самовывоз"])
        self.delivery_method.setMinimumHeight(35)
        self.delivery_method.currentTextChanged.connect(self.on_delivery_method_changed)
        delivery_layout.addWidget(self.delivery_method)
        
        # Контейнер для динамических полей
        self.dynamic_fields_widget = QWidget()
        self.dynamic_fields_layout = QVBoxLayout(self.dynamic_fields_widget)
        self.dynamic_fields_layout.setContentsMargins(0, 0, 0, 0)
        
        # Поле для адреса доставки (для курьера)
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Адрес доставки")
        self.address_input.setMaximumHeight(80)
        self.address_input.setMinimumHeight(60)
        self.dynamic_fields_layout.addWidget(self.address_input)
        
        # Поле для пункта выдачи (для самовывоза)
        self.pickup_point_combo = QComboBox()
        self.pickup_point_combo.setMinimumHeight(35)
        self.update_pickup_points()
        self.dynamic_fields_layout.addWidget(self.pickup_point_combo)
        
        # Информация о пункте выдачи
        self.pickup_info_label = QLabel()
        self.pickup_info_label.setStyleSheet("color: #2c3e50; font-size: 10px; padding: 5px;")
        self.pickup_info_label.setWordWrap(True)
        self.dynamic_fields_layout.addWidget(self.pickup_info_label)
        self.pickup_point_combo.currentTextChanged.connect(self.update_pickup_info)
        
        delivery_layout.addWidget(self.dynamic_fields_widget)
        
        # Показываем поле для курьера по умолчанию
        self.address_input.show()
        self.pickup_point_combo.hide()
        self.pickup_info_label.hide()
        
        delivery_group.setLayout(delivery_layout)
        layout.addWidget(delivery_group)
        
        self.order_btn = QPushButton("Оформить заказ")
        self.order_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                font-size: 14px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        self.order_btn.clicked.connect(self.place_order)
        layout.addWidget(self.order_btn)
        
        self.setLayout(layout)
    
    def update_pickup_points(self):
        """Обновляет список пунктов выдачи"""
        self.pickup_point_combo.clear()
        for point in self.pickup_points:
            self.pickup_point_combo.addItem(point.name, point.id)
    
    def update_pickup_info(self, point_name):
        """Обновляет информацию о выбранном пункте выдачи"""
        for point in self.pickup_points:
            if point.name == point_name:
                self.pickup_info_label.setText(f"📍 {point.address}\n🕐 {point.working_hours}")
                break
    
    def on_delivery_method_changed(self, method):
        """Показывает/скрывает поля в зависимости от способа доставки"""
        if method == "Курьером":
            self.address_input.show()
            self.pickup_point_combo.hide()
            self.pickup_info_label.hide()
        else:  # Самовывоз
            self.address_input.hide()
            self.pickup_point_combo.show()
            self.pickup_info_label.show()
            self.update_pickup_info(self.pickup_point_combo.currentText())
    
    def update_summary(self):
        items, total = self.get_cart_summary_callback()
        if not items:
            self.order_text.setText("Корзина пуста")
            return
        summary = "Ваш заказ:\n\n"
        for item in items:
            summary += f"{item['name']} x {item['quantity']} = {item['subtotal']} руб.\n"
        summary += f"\nИтого: {total} руб."
        self.order_text.setText(summary)
    
    def place_order(self):
        items, total = self.get_cart_summary_callback()
        if not items:
            QMessageBox.warning(self, "Ошибка", "Корзина пуста")
            return
        
        if not self.name_input.text() or not self.phone_input.text():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните ФИО и телефон")
            return
        
        delivery_method = self.delivery_method.currentText()
        address = ""
        pickup_point_id = None
        
        if delivery_method == "Курьером":
            if not self.address_input.toPlainText():
                QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите адрес доставки")
                return
            address = self.address_input.toPlainText()
        else:  # Самовывоз
            pickup_point_id = self.pickup_point_combo.currentData()
            # Получаем адрес пункта выдачи
            for point in self.pickup_points:
                if point.id == pickup_point_id:
                    address = f"Пункт выдачи: {point.name}, {point.address}"
                    break
        
        # Получаем ID пользователя
        user_manager = UserManager()
        user_id = user_manager.get_user_id(self.username)
        user_manager.close()
        
        # Сохраняем заказ в БД
        order_manager = OrderManager()
        success = order_manager.save_order(
            user_id=user_id,
            user_name=self.username,
            items=items,
            total=total,
            recipient_name=self.name_input.text(),
            address=address,
            phone=self.phone_input.text(),
            delivery_method=delivery_method,
            pickup_point_id=pickup_point_id
        )
        order_manager.close()
        
        if not success:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить заказ")
            return
        
        order_info = f"Заказ оформлен!\n\n"
        order_info += f"Получатель: {self.name_input.text()}\n"
        order_info += f"Телефон: {self.phone_input.text()}\n"
        order_info += f"Способ доставки: {delivery_method}\n"
        order_info += f"Адрес: {address}\n\n"
        order_info += f"Состав заказа:\n"
        for item in items:
            order_info += f"- {item['name']} x {item['quantity']} = {item['subtotal']} руб.\n"
        
        order_info += f"\nИтого к оплате: {total} руб."
        QMessageBox.information(self, "Заказ оформлен", order_info)
        
        # Очищаем корзину после оформления заказа
        self.clear_cart_callback()
        self.name_input.clear()
        self.address_input.clear()
        self.phone_input.clear()
        self.update_summary()

class OrdersTab(QWidget):
    """Вкладка для просмотра всех заказов (только для продавцов)"""
    def __init__(self):
        super().__init__()
        self.order_manager = OrderManager()
        layout = QVBoxLayout()
        
        title = QLabel("Все заказы")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #9B59B6;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        refresh_btn = QPushButton("Обновить список заказов")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                font-size: 12px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_orders)
        layout.addWidget(refresh_btn)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Пользователь", "Дата", "Сумма (руб)", 
            "Получатель", "Адрес", "Телефон", "Способ доставки", "Пункт выдачи"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_orders()
    
    def refresh_orders(self):
        """Обновляет таблицу с заказами"""
        orders = self.order_manager.get_all_orders()
        
        if not orders:
            self.table.setRowCount(1)
            self.table.setSpan(0, 0, 1, 9)
            
            message_item = QTableWidgetItem("📦 Заказов нет")
            message_item.setTextAlignment(Qt.AlignCenter)
            message_item.setFont(QFont("Arial", 14, QFont.Bold))
            message_item.setForeground(Qt.gray)
            
            self.table.setItem(0, 0, message_item)
            
            for col in range(1, 9):
                self.table.setItem(0, col, QTableWidgetItem(""))
            
            if self.parent():
                self.parent().setWindowTitle(f"Интернет-магазин - Заказов: 0")
            return
        
        self.table.clearSpans()
        self.table.setRowCount(len(orders))
        
        for row, order in enumerate(orders):
            self.table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            self.table.setItem(row, 1, QTableWidgetItem(order.user_name))
            self.table.setItem(row, 2, QTableWidgetItem(order.order_date.strftime("%d.%m.%Y %H:%M")))
            self.table.setItem(row, 3, QTableWidgetItem(str(order.total)))
            self.table.setItem(row, 4, QTableWidgetItem(order.recipient_name))
            self.table.setItem(row, 5, QTableWidgetItem(order.address))
            self.table.setItem(row, 6, QTableWidgetItem(order.phone))
            self.table.setItem(row, 7, QTableWidgetItem(order.delivery_method))
            
            pickup_info = ""
            if order.pickup_point:
                pickup_info = order.pickup_point.name
            self.table.setItem(row, 8, QTableWidgetItem(pickup_info))
        
        if self.parent():
            self.parent().setWindowTitle(f"Интернет-магазин - Заказов: {len(orders)}")

class AdminTab(QWidget):
    """Вкладка для управления продавцами (только для админа)"""
    def __init__(self):
        super().__init__()
        self.user_manager = UserManager()
        self.init_ui()
        self.refresh_sellers()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Управление продавцами")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #9B59B6;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Группа создания продавца
        create_group = QGroupBox("Создать нового продавца")
        create_layout = QVBoxLayout()
        
        self.new_login = QLineEdit()
        self.new_login.setPlaceholderText("Логин продавца")
        create_layout.addWidget(self.new_login)
        
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("Пароль")
        self.new_password.setEchoMode(QLineEdit.Password)
        create_layout.addWidget(self.new_password)
        
        create_btn = QPushButton("Создать продавца")
        create_btn.clicked.connect(self.create_seller)
        create_layout.addWidget(create_btn)
        
        create_group.setLayout(create_layout)
        layout.addWidget(create_group)
        
        # Таблица продавцов
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Логин", "Пункт выдачи", "Действия"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh_sellers(self):
        """Обновляет таблицу продавцов"""
        sellers = self.user_manager.get_all_sellers()
        pickup_points = self.user_manager.get_all_pickup_points()
        
        self.table.setRowCount(len(sellers))
        
        for row, seller in enumerate(sellers):
            self.table.setItem(row, 0, QTableWidgetItem(str(seller.id)))
            self.table.setItem(row, 1, QTableWidgetItem(seller.username))
            
            # ComboBox для выбора пункта выдачи
            combo = QComboBox()
            for point in pickup_points:
                combo.addItem(point.name, point.id)
            
            # Устанавливаем текущий пункт выдачи
            if seller.pickup_point_id:
                index = combo.findData(seller.pickup_point_id)
                if index >= 0:
                    combo.setCurrentIndex(index)
            
            combo.currentIndexChanged.connect(lambda _, sid=seller.id, c=combo: self.change_pickup_point(sid, c))
            self.table.setCellWidget(row, 2, combo)
            
            # Кнопка удаления
            delete_btn = QPushButton("Удалить")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E74C3C;
                }
                QPushButton:hover {
                    background-color: #C0392B;
                }
            """)
            delete_btn.clicked.connect(lambda _, sid=seller.id: self.delete_seller(sid))
            self.table.setCellWidget(row, 3, delete_btn)
    
    def create_seller(self):
        """Создает нового продавца"""
        login = self.new_login.text().strip()
        password = self.new_password.text().strip()
        
        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        
        if len(password) < 4:
            QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 4 символов")
            return
        
        # Получаем первый пункт выдачи
        pickup_points = self.user_manager.get_all_pickup_points()
        pickup_id = pickup_points[0].id if pickup_points else None
        
        if self.user_manager.add_user(login, password, 'seller', pickup_id):
            QMessageBox.information(self, "Успешно", f"Продавец {login} создан!")
            self.new_login.clear()
            self.new_password.clear()
            self.refresh_sellers()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось создать продавца")
    
    def change_pickup_point(self, seller_id, combo):
        """Изменяет пункт выдачи продавца"""
        pickup_id = combo.currentData()
        if pickup_id:
            self.user_manager.update_seller_pickup_point(seller_id, pickup_id)
    
    def delete_seller(self, seller_id):
        """Удаляет продавца"""
        reply = QMessageBox.question(self, "Подтверждение", 
                                    "Вы уверены, что хотите удалить этого продавца?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, message = self.user_manager.delete_seller(seller_id)
            if success:
                QMessageBox.information(self, "Успешно", message)
                self.refresh_sellers()
            else:
                QMessageBox.warning(self, "Ошибка", message)

class PickupPointsTab(QWidget):
    """Вкладка для управления пунктами выдачи (только для админа)"""
    def __init__(self):
        super().__init__()
        self.user_manager = UserManager()
        self.init_ui()
        self.refresh_points()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Управление пунктами выдачи")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #9B59B6;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Группа создания пункта выдачи
        create_group = QGroupBox("Добавить пункт выдачи")
        create_layout = QVBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название пункта выдачи")
        create_layout.addWidget(self.name_input)
        
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Адрес")
        create_layout.addWidget(self.address_input)
        
        self.hours_input = QLineEdit()
        self.hours_input.setPlaceholderText("Часы работы (например: Пн-Пт 9:00-20:00)")
        create_layout.addWidget(self.hours_input)
        
        create_btn = QPushButton("Добавить пункт выдачи")
        create_btn.clicked.connect(self.create_pickup_point)
        create_layout.addWidget(create_btn)
        
        create_group.setLayout(create_layout)
        layout.addWidget(create_group)
        
        # Таблица пунктов выдачи с кнопкой удаления
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Адрес", "Часы работы", "Действия"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh_points(self):
        """Обновляет таблицу пунктов выдачи"""
        points = self.user_manager.get_all_pickup_points()
        
        self.table.setRowCount(len(points))
        
        for row, point in enumerate(points):
            self.table.setItem(row, 0, QTableWidgetItem(str(point.id)))
            self.table.setItem(row, 1, QTableWidgetItem(point.name))
            self.table.setItem(row, 2, QTableWidgetItem(point.address))
            self.table.setItem(row, 3, QTableWidgetItem(point.working_hours))
            
            # Кнопка удаления
            delete_btn = QPushButton("Удалить")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E74C3C;
                }
                QPushButton:hover {
                    background-color: #C0392B;
                }
            """)
            delete_btn.clicked.connect(lambda _, pid=point.id: self.delete_pickup_point(pid))
            self.table.setCellWidget(row, 4, delete_btn)
    
    def create_pickup_point(self):
        """Создает новый пункт выдачи"""
        name = self.name_input.text().strip()
        address = self.address_input.text().strip()
        hours = self.hours_input.text().strip()
        
        if not name or not address or not hours:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        
        if self.user_manager.add_pickup_point(name, address, hours):
            QMessageBox.information(self, "Успешно", "Пункт выдачи добавлен!")
            self.name_input.clear()
            self.address_input.clear()
            self.hours_input.clear()
            self.refresh_points()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить пункт выдачи")
    
    def delete_pickup_point(self, point_id):
        """Удаляет пункт выдачи"""
        reply = QMessageBox.question(self, "Подтверждение", 
                                    "Вы уверены, что хотите удалить этот пункт выдачи?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, message = self.user_manager.delete_pickup_point(point_id)
            if success:
                QMessageBox.information(self, "Успешно", message)
                self.refresh_points()
            else:
                QMessageBox.warning(self, "Ошибка", message)

class ProductsManagementTab(QWidget):
    """Вкладка для управления товарами (для админа и продавцов)"""
    def __init__(self, product_manager, role):
        super().__init__()
        self.product_manager = product_manager
        self.role = role
        self.init_ui()
        self.refresh_products()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Управление товарами")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #9B59B6;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Группа добавления товара
        add_group = QGroupBox("Добавить новый товар")
        add_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название товара")
        add_layout.addWidget(self.name_input)
        
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Цена (руб)")
        self.price_input.setFixedWidth(120)
        add_layout.addWidget(self.price_input)
        
        self.stock_input = QSpinBox()
        self.stock_input.setMinimum(0)
        self.stock_input.setMaximum(9999)
        self.stock_input.setValue(10)
        self.stock_input.setPrefix("Количество: ")
        add_layout.addWidget(self.stock_input)
        
        add_btn = QPushButton("Добавить товар")
        add_btn.clicked.connect(self.add_product)
        add_layout.addWidget(add_btn)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Таблица товаров
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Цена (руб)", "В наличии", "Редактировать", "Удалить"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh_products(self):
        """Обновляет таблицу товаров"""
        products = self.product_manager.get_all_products()
        
        self.table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(str(product["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(product["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(product["price"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(product["stock"])))
            
            # Кнопка редактирования
            edit_btn = QPushButton("✏️ Редактировать")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            edit_btn.clicked.connect(lambda _, pid=product["id"]: self.edit_product(pid))
            self.table.setCellWidget(row, 4, edit_btn)
            
            # Кнопка удаления
            delete_btn = QPushButton("🗑️ Удалить")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E74C3C;
                }
                QPushButton:hover {
                    background-color: #C0392B;
                }
            """)
            delete_btn.clicked.connect(lambda _, pid=product["id"]: self.delete_product(pid))
            self.table.setCellWidget(row, 5, delete_btn)
    
    def add_product(self):
        """Добавляет новый товар"""
        name = self.name_input.text().strip()
        price_text = self.price_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название товара")
            return
        
        try:
            price = float(price_text)
            if price < 0:
                raise ValueError("Цена не может быть отрицательной")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректную цену")
            return
        
        stock = self.stock_input.value()
        
        if self.product_manager.add_product(name, price, stock):
            QMessageBox.information(self, "Успешно", f"Товар '{name}' добавлен!")
            self.name_input.clear()
            self.price_input.clear()
            self.stock_input.setValue(10)
            self.refresh_products()
            # Обновляем список товаров в основном окне
            if self.parent() and hasattr(self.parent(), 'products_tab'):
                self.parent().products_tab.products = self.product_manager.get_all_products()
                self.parent().products_tab.update_products_table()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить товар")
    
    def edit_product(self, product_id):
        """Открывает диалог редактирования товара"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование товара: {product['name']}")
        dialog.setModal(True)
        dialog.setFixedSize(400, 250)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        name_edit = QLineEdit(product["name"])
        form_layout.addRow("Название:", name_edit)
        
        price_edit = QLineEdit(str(product["price"]))
        form_layout.addRow("Цена (руб):", price_edit)
        
        stock_edit = QSpinBox()
        stock_edit.setMinimum(0)
        stock_edit.setMaximum(9999)
        stock_edit.setValue(product["stock"])
        form_layout.addRow("Количество:", stock_edit)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            name = name_edit.text().strip()
            price_text = price_edit.text().strip()
            
            if not name:
                QMessageBox.warning(self, "Ошибка", "Введите название товара")
                return
            
            try:
                price = float(price_text)
                if price < 0:
                    raise ValueError("Цена не может быть отрицательной")
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Введите корректную цену")
                return
            
            stock = stock_edit.value()
            
            if self.product_manager.update_product(product_id, name, price, stock):
                QMessageBox.information(self, "Успешно", "Товар обновлен!")
                self.refresh_products()
                # Обновляем список товаров в основном окне
                if self.parent() and hasattr(self.parent(), 'products_tab'):
                    self.parent().products_tab.products = self.product_manager.get_all_products()
                    self.parent().products_tab.update_products_table()
                # Обновляем корзину
                if self.parent() and hasattr(self.parent(), 'cart_tab'):
                    self.parent().cart_tab.update_cart_table()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить товар")
    
    def delete_product(self, product_id):
        """Удаляет товар"""
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            return
        
        # Проверяем, есть ли товар в заказах (сохраненных в БД)
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            engine = create_engine('sqlite:///online_store.db', echo=False)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Проверяем, есть ли товар в заказах (хранятся в JSON)
            # Это сложная проверка, так как товары хранятся в JSON-поле
            # Для простоты пропускаем эту проверку в демо-версии
            
            session.close()
            
        except Exception as e:
            print(f"Ошибка при проверке заказов: {e}")
        
        reply = QMessageBox.question(
            self, 
            "Подтверждение удаления", 
            f"Вы уверены, что хотите удалить товар '{product['name']}'?\n\n"
            "Внимание: если этот товар есть в чьих-то корзинах, "
            "он будет удален оттуда автоматически.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Удаляем товар из всех корзин через прямой запрос к БД
            try:
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                
                engine = create_engine('sqlite:///online_store.db', echo=False)
                Session = sessionmaker(bind=engine)
                session = Session()
                
                # Удаляем товар из всех корзин
                deleted_count = session.query(Cart).filter_by(product_id=product_id).delete()
                session.commit()
                session.close()
                
                if deleted_count > 0:
                    print(f"Товар удален из {deleted_count} корзин")
                
            except Exception as e:
                print(f"Ошибка при удалении товара из корзин: {e}")
            
            # Удаляем товар из списка товаров
            if self.product_manager.delete_product(product_id):
                QMessageBox.information(self, "Успешно", f"Товар '{product['name']}' удален!")
                self.refresh_products()
                # Обновляем список товаров в основном окне
                if self.parent() and hasattr(self.parent(), 'products_tab'):
                    self.parent().products_tab.products = self.product_manager.get_all_products()
                    self.parent().products_tab.update_products_table()
                # Обновляем корзину
                if self.parent() and hasattr(self.parent(), 'cart_tab'):
                    self.parent().cart_tab.update_cart_table()
                # Обновляем корзину пользователя
                if self.parent() and hasattr(self.parent(), 'cart'):
                    # Удаляем товар из текущей корзины пользователя
                    if product_id in self.parent().cart:
                        del self.parent().cart[product_id]
                        if hasattr(self.parent(), 'cart_tab'):
                            self.parent().cart_tab.update_cart_table()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить товар")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()