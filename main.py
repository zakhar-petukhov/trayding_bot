import logging
from datetime import datetime

import flask
import os
import telebot
from coinpayments import CoinPaymentsAPI
from dateutil.relativedelta import relativedelta

from app import app, db
from config import *
from models import User, Deposit

token = TOKEN
bot = telebot.TeleBot(token)

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

api = CoinPaymentsAPI(private_key=PRIVATE_KEY, public_key=PUBLIC_KEY)
exec_path = os.getcwd()


@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''

    elif flask.request.headers.get('content-type') == 'application/x-www-form-urlencoded; charset=utf-8':
        print()
        a = CoinPay()
        request_from_api = flask.request.values
        print(request_from_api)
        print()
        address = request_from_api['address']
        status = request_from_api['status_text']
        amount = request_from_api['amount']
        a.comparison_bitcoin_address(address, status, amount)
        print(address, status, amount)
        return ''

    else:
        flask.abort(403)


def english_button(user_id):
    user_markup_keyboard = telebot.types.ReplyKeyboardMarkup(True)
    user_markup_keyboard.row('💰 Balance')
    user_markup_keyboard.row('Deposit 📥', 'Withdraw 📤')
    user_markup_keyboard.row('Reinvest ♻️', 'Referral system 👨‍👩‍👧‍👦')
    user_markup_keyboard.add('History 📚', 'Help 💡')
    return user_markup_keyboard


class UpdateUser:
    def __init__(self, user_id):
        self.user_id = user_id
        self.update_db = User.query.filter(User.user_id == user_id).first()

    def create_user(self):
        bitcoin_address = api.get_callback_address(currency='BTC', ipn_url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)
        try:
            if self.update_db is None:
                new_user = User(user_id=self.user_id, bitcoin_address=bitcoin_address['result']['address'])
                db.session.add(new_user)
                db.session.commit()
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()


class CoinPay:
    def comparison_bitcoin_address(self, bitcoin_address, status, amount):
        print(bitcoin_address, status, amount)
        comparison_bitcoin_address = User.query.filter(User.bitcoin_address ==
                                                         '{}'.format(bitcoin_address)).first()
        try:
            if (bitcoin_address == comparison_bitcoin_address.bitcoin_address) and (status == 'Deposit confirmed'):
                if comparison_bitcoin_address.referal_user is not None:
                    ref_balance = User.query.filter(User.user_id == int('{}'.format(
                        comparison_bitcoin_address.referal_user))).first()
                    print(ref_balance)
                    ref_balance.balance = format(float(ref_balance.balance) + float(amount) * 0.03, '.8f')
                    comparison_bitcoin_address.referal_user = None
                    db.session.add(ref_balance, comparison_bitcoin_address)
                    db.session.commit()
                zero_number = '0.00000000'
                amount_for_deposit = format(float(amount) + float(zero_number), '.8f')
                deposit_percent = format(float(amount) * 0.01, '.8f')
                user_id = comparison_bitcoin_address.user_id
                date_create = datetime.now().strftime('%d.%m.%Y')
                date_withdraw = datetime.now()+ relativedelta(days=30)
                deposit = Deposit(deposit_id=user_id, deposit=amount_for_deposit,
                deposit_with_percent=deposit_percent, data_create=date_create,
                data_withdraw=date_withdraw.strftime('%d.%m.%Y'))
                db.session.add(deposit)
                db.session.commit()
                bot.send_message(chat_id=user_id, text='Funds credited to your account.')

            else:
                print('error')
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()


@bot.message_handler(commands=['start'])
def start_handler(message):
    text = message.text
    user_id = message.from_user.id
    refferal_user = text.split(' ')
    old_user = message.from_user.username
    try:
        chat_id = message.chat.id
        update_db = UpdateUser(user_id)
        update_db.create_user()
        if len(refferal_user) == 2 and int(refferal_user[1]) != user_id:
            database = User.query.filter(User.user_id == user_id).first()
            if database.referal_user != refferal_user[1]:
                bot.send_message(chat_id=refferal_user[1], text='This user @{} clicked on your link'.format(old_user))
            database.referal_user = refferal_user[1]
            db.session.add(database)
            db.session.commit()
        bot.send_message(chat_id, '''
The official Telegram Bot of SAMSON FUND , a cryptocurrency investment fund. 

1⃣ 1% profit daily

2⃣ Commissions on new deposit only

3⃣ Referral commssion 3%

4⃣ This is LONG term, slow growth

5⃣ All contracts are paid from From Trading.

For more information about the Fund, 
Message: @samsonceo''', parse_mode='markdown', reply_markup=english_button(user_id))
    except:
        db.session.rollback()
        raise
    finally:
        db.session.close()


@bot.callback_query_handler(func=lambda button: True)
def selection_of_buttons(button):
    chat_id = button.message.chat.id
    message_id = button.message.message_id
    text_button = button.data.split(' ')
    user_id = text_button[3]
    amount = text_button[9]
    if button.data:
        try:
            database = User.query.filter(User.user_id == int(user_id)).first()
            database.balance = format(float(database.balance) - float(amount), '.8f')
            db.session.add(database)
            db.session.commit()
            bot.edit_message_text(text='*User balance changed.*', chat_id=chat_id, message_id=message_id,
                                  parse_mode='markdown')
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()


@bot.message_handler(func=lambda message: True, content_types=['text'])
def start_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text
    if text == 'Deposit 📥':
        try:
            database = User.query.filter(User.user_id == user_id).first()
            bot.send_message(chat_id, text='''
📥 *Deposit* 📥

You can make a deposit in the bot's wallet, for this use the wallet that the bot generated for you (minimum 0.01 BTC).
 
After making a deposit, your funds will be shown on the balance tab. A transaction can take 30 - 40 minutes depending on the server load.

You will receive a message about enrollment.

Thank you for using this Samsonfund Trading Bot!''', parse_mode='markdown')
            bot.send_message(chat_id, '*Address:* `{}`'.format(database.bitcoin_address), parse_mode='markdown')
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()

    if text == 'Help 💡':
        bot.send_message(chat_id, text='''
💡 *Help* 💡

This is the official Telegram Bot of SAMSON FUND , a cryptocurrency investment fund. 

*Join us community chatroom:* @samsonfundchat

For more information about the Fund, 
*Message:* @samsonceo''', parse_mode='markdown')

    if text == '💰 Balance':
        database_deposit = Deposit.query.filter(Deposit.deposit_id == user_id).all()
        user = User.query.filter(User.user_id == user_id).first()
        try:
            all_deposits = [i.deposit for i in database_deposit]
            all_deposits_with_commissions = [i.deposit_with_percent for i in database_deposit]
            if database_deposit:
                bot.send_message(chat_id, text='''
💰 *Balance* 💰

*Deposits created:*
{} BTC

*Earnings accurals:*
{} BTC

*Available for Withdraw*
{} BTC'''.format(' BTC \n'.join(all_deposits), ' BTC \n'.join(all_deposits_with_commissions), user.balance),
                             parse_mode='markdown')
            else:
                bot.send_message(chat_id, text='''
💰 *Balance* 💰

*Deposits created:*
0.00000000 BTC

*Earnings accurals:*
0.00000000 BTC

*Available for Withdraw*
0.00000000 BTC''', parse_mode='markdown')

        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()

    if text == 'History 📚':
        database_deposit = Deposit.query.filter(Deposit.deposit_id == user_id).all()
        try:
            if database_deposit:
                all_deposits = [i.deposit for i in database_deposit]
                all_deposits_with_commissions = [i.deposit_with_percent for i in database_deposit]
                data_create = [i.data_create for i in database_deposit]
                data_withdraw = [i.data_withdraw for i in database_deposit]
                keys = ['*Deposit*', 'Earnings accurals', 'Data create', 'Data withdraw']
                zipped = zip(all_deposits, all_deposits_with_commissions, data_create, data_withdraw)
                dicts = [dict(zip(keys, values)) for values in zipped]
                transaktion_history = "*Your transaction history:*\n"
                for i in dicts:
                    for key, value in i.items():
                        transaktion_history += key + ": " + value + ", "
                    transaktion_history += "\n"

                bot.send_message(chat_id, text='''
📚 *History* 📚

{}'''.format(transaktion_history), parse_mode='markdown')

            else:
                bot.send_message(chat_id, "You haven't made a deposit yet")
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()


    if text == 'Withdraw 📤':
        user = User.query.filter(User.user_id == user_id).first()
        try:
            if not format(float(user.balance), '.8f') == format(float(0.00000000), '.8f'):
                msg = bot.send_message(chat_id, text='''
How many Bitcoins do you want to get out? Minimum output amount 0.005 BTC
Write in the format of the number of bitcoins through commas of your wallet.
*Example:* `0.005, 3J1sYC4B4JH9bQfx9r7HqKLKNoSoGspxR5`''', parse_mode='markdown')
                bot.register_next_step_handler(msg, withdraw_btc)
            else:
                bot.send_message(chat_id, text="You don't have any open deposits")
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()

    if text == 'Reinvest ♻️':
        database_user = User.query.filter(User.user_id == user_id).first()
        try:
            balance_for_reinvest = database_user.balance
            if not format(float(balance_for_reinvest), '.8f') == format(float(0.00000000), '.8f'):
                msg = bot.send_message(chat_id, "How much do you want to reinvest (minimum 0.01 BTC)?")
                bot.register_next_step_handler(msg, reinvest_btc)
            else:
                bot.send_message(chat_id, "You can't make a reinvest")
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()

    if text == 'Referral system 👨‍👩‍👧‍👦':
        database_user = User.query.filter(User.user_id == user_id).first()
        try:
            refferal_user_id = database_user.user_id
            create_refferal_url = 'http://t.me/SamsonfundTradingBot?start={}'.format(refferal_user_id)
            bot.send_message(chat_id, '''
After the user makes the first deposit, you will receive 3% of the balance.
*Your Referral Link to share with your Friends:*''', parse_mode='markdown')
            bot.send_message(chat_id, create_refferal_url)
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()


def withdraw_btc(message):
    chat_id = message.chat.id
    text = message.text
    money_and_wallet = text.split(', ')
    message_id = message.message_id
    user_id = message.from_user.id
    user = User.query.filter(User.user_id == user_id).first()
    transfer_confirmation = ['The transfer of {} user to the amount of {} BTC'.format(user_id, money_and_wallet[0])]
    try:
        if format(float(money_and_wallet[0]), '.8f') >= format(float('0.00500000'), '.8f'):
            if format(float(money_and_wallet[0]), '.8f') <= format(float(user.balance), '.8f'):
                user_markup_inline = telebot.types.InlineKeyboardMarkup(True)
                user_markup_inline.add(*[telebot.types.InlineKeyboardButton(text=name, callback_data=name)
                                         for name in transfer_confirmation])
                bot.send_message(chat_id, '''The withdraw is done manually, your data has been transferred to the administrator.''')
                bot.forward_message(763676510, chat_id, message_id)
                bot.send_message(763676510, text='{}'.format(user.balance), reply_markup=user_markup_inline)
            else:
                bot.send_message(chat_id, 'The operation failed, check the correct spelling.')
        else:
            bot.send_message(chat_id, text='Minimum withdrawal amount 0.005 BTC')
    except:
        db.session.rollback()
        bot.send_message(chat_id, 'The operation failed, check the correct spelling.')
    finally:
        db.session.close()


def reinvest_btc(message):
    chat_id = message.chat.id
    amount = message.text
    user_id = message.from_user.id
    database_user = User.query.filter(User.user_id == user_id).first()
    try:
        zero_number = '0.00000000'
        amount_for_deposit = format(float(amount) + float(zero_number), '.8f')
        balance_for_reinvest = database_user.balance
        if format(float(amount_for_deposit), '.8f') >= format(float('0.01000000'), '.8f'):
            if format(float(amount_for_deposit), '.8f') <= format(float(balance_for_reinvest), '.8f'):
                date_create = datetime.now().strftime('%d.%m.%Y')
                date_withdraw = datetime.now() + relativedelta(days=30)
                deposit = Deposit(deposit_id=user_id, deposit=amount_for_deposit,
                                  deposit_with_percent=amount_for_deposit, data_create=date_create,
                                  data_withdraw=date_withdraw.strftime('%d.%m.%Y'))
                database_user.balance = format(float(database_user.balance) - float(amount_for_deposit), '.8f')
                db.session.add(deposit, database_user)
                db.session.commit()
                bot.send_message(chat_id=user_id, text='A new deposit has been created.')
            else:
                bot.send_message(chat_id, "You've specified more than you have on your balance.")
        else:
            bot.send_message(chat_id, text='Minimum reinvestment amount 0.01 BTC')
    except:
        db.session.rollback()
        bot.send_message(chat_id, 'The operation failed, check the correct spelling.')
    finally:
        db.session.close()


bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))


if __name__ == '__main__':
    app.run(host=WEBHOOK_LISTEN,
            port=WEBHOOK_PORT,
            ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)
            )



