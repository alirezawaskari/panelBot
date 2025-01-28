from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, LargeBinary, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker, relationship

from config import DATABASE_URL


Base = declarative_base()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# User Model
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, default=0.0)
    banned = Column(Boolean, default=False)

    orders = relationship("Order", back_populates="user")

    def add_balance(self, db_session: Session, amount: float):
        """Increase the balance by the given amount."""
        self.balance += amount
        db_session.commit()

    def subtract_balance(self, db_session: Session, amount: float):
        """Decrease the balance by the given amount."""
        self.balance -= amount
        db_session.commit()

    def toggle_ban(self, db_session: Session):
        """Toggle the user's ban status."""
        self.banned = not self.banned
        db_session.commit()

    @staticmethod
    def get_users(db_session: Session, page: int = 1, page_size: int = 10):
        """Fetch users with pagination."""
        skip = (page - 1) * page_size
        return db_session.query(User).offset(skip).limit(page_size).all()

    @staticmethod
    def get_user(db_session: Session, user_id: int):
        """Fetch a user and their statistics like balance, ban status, and order count."""
        user = db_session.query(User).filter(User.user_id == user_id).first()
        if user:
            order_count = db_session.query(Order).filter(
                Order.user_id == user_id).count()
            user_stats = {
                "user_id": user.user_id,
                "balance": user.balance,
                "banned": user.banned,
                "order_count": order_count
            }
            return user, user_stats
        return None, None


# Admin Model
class Admin(Base):
    __tablename__ = 'admins'
    admin_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)

    user = relationship("User", back_populates="admins")

    def add_admin(self, db_session: Session, user: User):
        """Add a user as an admin and commit the changes."""
        self.user = user
        db_session.add(self)
        db_session.commit()

    def remove_admin(self, db_session: Session):
        """Remove the admin role from a user and commit the changes."""
        self.user = None
        db_session.commit()

    @staticmethod
    def get_admins(db_session: Session, page: int = 1, page_size: int = 10):
        """List admins with pagination."""
        skip = (page - 1) * page_size
        return db_session.query(Admin).offset(skip).limit(page_size).all()


# Order status Enum
class OrderStatus(PyEnum):
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


# Order Model
class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    status = Column(PyEnum(OrderStatus), default=OrderStatus.in_progress)
    product_id = Column(Integer, ForeignKey('products.product_id'))
    price = Column(Float)
    order_date = Column(DateTime, default=func.now())

    product = relationship("Product", back_populates="orders")
    user = relationship("User", back_populates="orders")

    def complete(self, db_session: Session):
        """Mark order as completed."""
        self.status = OrderStatus.completed
        db_session.commit()

    def cancel(self, db_session: Session):
        """Mark order as cancelled."""
        self.status = OrderStatus.cancelled
        db_session.commit()

    @staticmethod
    def get_order(db_session: Session, order_id: int):
        """Search for an order by its ID along with its status and other details."""
        order = db_session.query(Order).filter(
            Order.order_id == order_id).first()
        if order:
            order_info = {
                "order_id": order.order_id,
                "status": order.status.value,
                "user_id": order.user_id,
                "product_id": order.product_id,
                "price": order.price,
                "order_date": order.order_date
            }
            return order_info
        return None

    @staticmethod
    def get_orders(db_session: Session, page: int = 1, page_size: int = 10):
        """List orders that are in progress (current orders) with pagination."""
        skip = (page - 1) * page_size
        return db_session.query(Order).filter(Order.status == OrderStatus.in_progress).offset(skip).limit(page_size).all()

    @staticmethod
    def get_cancelled(db_session: Session, page: int = 1, page_size: int = 10):
        """List orders that are cancelled with pagination."""
        skip = (page - 1) * page_size
        return db_session.query(Order).filter(Order.status == OrderStatus.cancelled).offset(skip).limit(page_size).all()

    @staticmethod
    def get_completed(db_session: Session, page: int = 1, page_size: int = 10):
        """List orders that are completed with pagination."""
        skip = (page - 1) * page_size
        return db_session.query(Order).filter(Order.status == OrderStatus.completed).offset(skip).limit(page_size).all()

    @staticmethod
    def change_status(db_session: Session, order_id: int, new_status: OrderStatus):
        """Change the status of an order."""
        order = db_session.query(Order).filter(
            Order.order_id == order_id).first()
        if order:
            order.status = new_status
            db_session.commit()
            return True
        return False


# Product Model
class Product(Base):
    __tablename__ = 'products'
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(LargeBinary)
    price = Column(Float)

    def update_price(self, db_session: Session, new_price: float):
        """Update the price of the product."""
        self.price = new_price
        db_session.commit

    @staticmethod
    def get_product(db_session: Session, search_value: str):
        """Search a product by name or id."""
        if search_value.isdigit():
            return db_session.query(Product).filter(Product.product_id == int(search_value)).first()
        return db_session.query(Product).filter(Product.name.ilike(f"%{search_value}%")).all()

    @staticmethod
    def get_products(db_session: Session, page: int = 1, page_size: int = 10):
        """List all products with pagination."""
        skip = (page - 1) * page_size
        return db_session.query(Product).offset(skip).limit(page_size).all()

    @staticmethod
    def add_product(db_session: Session, name: str, description: bytes, price: float):
        """Add a new product."""
        new_product = Product(name=name, description=description, price=price)
        db_session.add(new_product)
        db_session.commit()
        return new_product

    @staticmethod
    def remove_product(db_session: Session, product_id: int):
        """Remove a product by id."""
        product_to_remove = db_session.query(Product).filter(
            Product.product_id == product_id).first()
        if product_to_remove:
            db_session.delete(product_to_remove)
            db_session.commit()
            return True
        return False

    def change_product(self, db_session: Session, new_name: str = None, new_price: float = None, new_description: bytes = None):
        """Change product details (name, price, description)."""
        if new_name:
            self.name = new_name
        if new_price:
            self.price = new_price
        if new_description:
            self.description = new_description
        db_session.commit()


# Config Model
class Config(Base):
    __tablename__ = 'config'

    option_name = Column(String, primary_key=True)
    option_value = Column(LargeBinary)

    @staticmethod
    def set_config(db_session: Session, option_name: str, option_value: bytes):
        """Set a configuration option."""
        config = db_session.query(Config).filter(
            Config.option_name == option_name).first()
        if config:
            config.option_value = option_value
        else:
            config = Config(option_name=option_name, option_value=option_value)
            db_session.add(config)
            db_session.commit()

    @staticmethod
    def get_config(db_session: Session, option_name: str):
        """Get a configuration option."""
        config = db_session.query(Config).filter(
            Config.option_name == option_name).first()
        if not config:
            raise OperationalError(f"Option '{option_name}' not found.")
        return config.option_value

    @staticmethod
    def disable_bot(db_session: Session):
        """Disable the bot."""
        Config.set_option(db_session, "disabled", b"True")

    @staticmethod
    def enable_bot(db_session: Session):
        """Enable the bot."""
        Config.set_option(db_session, "disabled", b"False")

    @staticmethod
    def change_channel(db_session: Session, new_log_chan_id: int):
        """Change the log channel ID."""
        Config.set_option(db_session, "log_chan_id",
                          str(new_log_chan_id).encode())

    @staticmethod
    def change_rules(db_session: Session, new_rules: bytes):
        """Change the rules."""
        Config.set_option(db_session, "rules", new_rules)

    @staticmethod
    def change_support(db_session: Session, new_support_msg: bytes):
        """Change the support message."""
        Config.set_option(db_session, "support_msg", new_support_msg)


# Initialize the database tables
def init_db():
    Base.metadata.create_all(bind=engine)


# Database session handler
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
