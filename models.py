from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # Initialize SQLAlchemy

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)

    # Define relationships
    wallets = db.relationship('Wallet', backref='user', lazy=True)
    piggy_banks = db.relationship('PiggyBank', backref='user', lazy=True)

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    current_amount = db.Column(db.Float, nullable=False, default=0)

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

class PiggyBank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    current_amount = db.Column(db.Float, nullable=False, default=0)


class UserCategory(db.Model):
    __tablename__ = 'user_category'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), primary_key=True)

    # Relationships
    user = db.relationship('User', back_populates='user_categories')
    category = db.relationship('Category', back_populates='user_categories')


class Jar(db.Model):
    __tablename__ = 'jars'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    label = db.Column(db.String(255), nullable=True)
    target_amount = db.Column(db.Numeric(10, 2), nullable=False)
    current_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)

    # Define relationships if needed
    user = db.relationship('User', back_populates='jars')
    allocations = db.relationship('Allocation', back_populates='jar')

    def __repr__(self):
        return f"<Jar(id={self.id}, user_id={self.user_id}, label={self.label}, target_amount={self.target_amount}, current_amount={self.current_amount})>"

class Allocation(db.Model):
    __tablename__ = 'allocations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pocket_money_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    jar_id = db.Column(db.Integer, db.ForeignKey('jars.id'), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    piggy_bank_id = db.Column(db.Integer, nullable=True)
    wallet_id = db.Column(db.Integer, nullable=True)

    # Define relationships if needed
    user = db.relationship('User', back_populates='allocations')
    jar = db.relationship('Jar', back_populates='allocations')

    def __repr__(self):
        return f"<Allocation(id={self.id}, pocket_money_id={self.pocket_money_id}, user_id={self.user_id}, amount={self.amount})>"

class PocketMoney(db.Model):
    __tablename__ = 'pocket_money'

    pocket_money_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    frequency = db.Column(db.Enum('daily', 'weekly', 'monthly'), nullable=True)
    day_of_month = db.Column(db.Integer, nullable=True)
    day_of_week = db.Column(db.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'), nullable=True)

    # Define the relationship to the User model
    user = db.relationship('User', back_populates='pocket_money')

    def __repr__(self):
        return f"<PocketMoney(id={self.pocket_money_id}, user_id={self.user_id}, amount={self.amount}, frequency={self.frequency})>"


class Spending(db.Model):
    __tablename__ = 'spendings'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    amount = db.Column(db.Numeric(10, 2))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    date = db.Column(db.Date, primary_key=True)
    time = db.Column(db.Time, primary_key=True)
    description = db.Column(db.Text)

    # Relationships
    user = db.relationship('User', backref='spendings')
    category = db.relationship('Category', backref='spendings')


class Notification(db.Model):
    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    notification_message = db.Column(db.Text, nullable=False)
    pocket_money_date = db.Column(db.DateTime, nullable=True)
    pocket_money_id = db.Column(db.Integer, nullable=True)

    # Define relationships
    user = db.relationship('User', back_populates='notifications')
    pocket_money = db.relationship('PocketMoney', back_populates='notifications')

    def __repr__(self):
        return f"<Notification(id={self.notification_id}, user_id={self.user_id}, message={self.notification_message})>"