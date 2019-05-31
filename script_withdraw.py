import time
from datetime import datetime

import schedule
import telebot

from app import db
from config import *
from models import User, Deposit

token = TOKEN
bot = telebot.TeleBot(token)


def every_day_update():
    print('update balance on 1 percent')
    database = db.session.query(Deposit).all()
    try:
        for deposit in database:
            if deposit.is_active == '+':
                update_balance = format(float(deposit.deposit_with_percent) + float(deposit.deposit) * 0.01
                                        , '.8f')
                deposit.deposit_with_percent = '{}'.format(update_balance)
                db.session.add(deposit)
                db.session.commit()
    except:
        db.session.rollback()
        raise
    finally:
        db.session.close()


def check_withdraw():
    print('check withdraw')
    database_for_user = db.session.query(Deposit).all()
    today = datetime.now().strftime('%d.%m.%Y')
    try:
        user_id = set([i.deposit_id for i in database_for_user])
        for id_for_user in list(user_id):
            database_deposit = db.session.query(Deposit.deposit_with_percent, Deposit.data_withdraw,
                                                Deposit.is_active, Deposit.deposit).filter(Deposit.deposit_id ==
                                                                                    id_for_user).all()
            for i in database_deposit:
                if (time.strptime(today, "%d.%m.%Y") >= time.strptime(i.data_withdraw, "%d.%m.%Y")) \
                        and (i.is_active == '+'):
                    user_balance = User.query.filter(User.user_id == id_for_user).first()
                    deposit = Deposit.query.filter(Deposit.deposit_id == id_for_user).all()
                    user_balance.balance = format(float(user_balance.balance) + float(i.deposit_with_percent) +
                                                  float(i.deposit), '.8f')
                    for status in deposit:
                        if time.strptime(status.data_withdraw, "%d.%m.%Y") <= time.strptime(today, "%d.%m.%Y"):
                            status.is_active = '-'
                            db.session.add(status)
                    db.session.commit()
                    db.session.close()
                else:
                    print('no active deposits')
    except:
        db.session.rollback()
        raise
    finally:
        db.session.close()


schedule.every().day.at("10:05").do(every_day_update)
schedule.every().day.at("10:02").do(check_withdraw)

# schedule.every(0.1).minutes.do(every_day_update)
# schedule.every(0.2).minutes.do(check_withdraw)

while True:
    schedule.run_pending()
    time.sleep(1)
