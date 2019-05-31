from app import db


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    bitcoin_address = db.Column(db.String(90), unique=True, default=None)
    balance = db.Column(db.String(10), default='0.00000000')
    referal_user = db.Column(db.TEXT, default=None)

    def __repr__(self):
        return '<user_id: {}>'.format(self.user_id)


class Deposit(db.Model):
    __tablename__ = 'deposit'
    id = db.Column(db.Integer, primary_key=True)
    deposit_id = db.Column(db.Integer)
    deposit = db.Column(db.String(10), default='0.00000000')
    deposit_with_percent = db.Column(db.String(10), default='0.00000000')
    data_create = db.Column(db.String(50))
    data_withdraw = db.Column(db.String(50))
    is_active = db.Column(db.String(1), default='+')
