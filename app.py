from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from datetime import datetime, timedelta
import datetime
from decimal import Decimal
import mysql.connector
import bcrypt


app = Flask(__name__)

app.secret_key = 'your_secret_key_here'

def create_db_connection():
    """Function to create a database connection and cursor."""
    # Replace these values with your actual database configuration
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'haslomaslo',
        'database': 'sys'
    }

    # Establish a connection to the database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    return connection, cursor

# Global variables to store connection and cursor
db_connection, mycursor = create_db_connection()

# Define User class and login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def update_wallet_current_amount(user_id, amount, cursor):
    cursor.execute("UPDATE wallets SET current_amount = current_amount - %s WHERE user_id = %s", (amount, user_id))
    cursor.connection.commit()

def get_last_spendings(user_id, limit=5):
    global mycursor
    mycursor.execute("SELECT amount, date, time, description FROM spendings WHERE user_id = %s ORDER BY date DESC, time DESC LIMIT %s", (user_id, limit))
    last_spendings = mycursor.fetchall()
    return last_spendings


def get_pocket_money_by_frequency(user_id, frequency, cursor):
    cursor.execute("SELECT pocket_money_id, amount, frequency, day_of_month, day_of_week FROM pocket_money WHERE user_id = %s AND frequency = %s", (user_id, frequency))
    result = cursor.fetchall()
    return result


def get_allocations_by_record_id(record_id, cursor):
    try:
        query = "SELECT jar_id, piggy_bank_id, wallet_id, amount FROM allocations WHERE pocket_money_id = %s"
        cursor.execute(query, (record_id,))
        allocations = cursor.fetchall()
        return allocations
    except mysql.connector.Error as err:
        print(f"Error fetching allocations: {err}")
        return None


def get_pocket_money_amount(pocket_money_id):
    mycursor.execute("SELECT amount FROM pocket_money WHERE pocket_money_id = %s", (pocket_money_id,))
    result = mycursor.fetchone()
    return result[0] if result else 0

def get_jars(user_id, cursor):
    cursor.execute("SELECT label, target_amount, current_amount FROM jars WHERE user_id = %s", (user_id,))
    user_jars = cursor.fetchall()
    return user_jars

def get_categories(cursor):
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    return categories

def get_user_by_id(user_id, cursor):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(user_data[0], user_data[2], user_data[1], user_data[4])
    return None

def get_piggy_bank_id(user_id):
    db_connection, mycursor = create_db_connection()
    try:
        # Execute SQL query to retrieve piggy bank ID for the user
        mycursor.execute("SELECT id FROM piggy_banks WHERE user_id = %s", (user_id,))
        result = mycursor.fetchone()
        if result:
            return result[0]  # Return the piggy bank ID
        else:
            raise ValueError(f"No piggy bank found for user ID {user_id}")
    finally:
        mycursor.close()
        db_connection.close()


def get_wallet_id(user_id):
    db_connection, mycursor = create_db_connection()
    try:
        # Execute SQL query to retrieve wallet ID for the user
        mycursor.execute("SELECT id FROM wallets WHERE user_id = %s", (user_id,))
        result = mycursor.fetchone()
        if result:
            return result[0]  # Return the wallet ID
        else:
            raise ValueError(f"No wallet found for user ID {user_id}")
    finally:
        mycursor.close()
        db_connection.close()

def delete_notification(mycursor, notification_id):
    """
    Delete a notification from the database for a given notification_id.

    Args:
        mycursor: The database cursor.
        notification_id (int): The ID of the notification to delete.

    Returns:
        int: The number of affected rows.
    """
    # Execute the delete statement
    mycursor.execute("DELETE FROM notifications WHERE notification_id = %s", (notification_id,))

    # Get the number of affected rows
    affected_rows = mycursor.rowcount

    # Log the result
    print(f"Attempted to delete notification ID {notification_id}, affected rows: {affected_rows}")

    return affected_rows



@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Create database connection and cursor
        db_connection, mycursor = create_db_connection()

        mycursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = mycursor.fetchone()
        if existing_user:
            flash('Error: Email already exists. Please use a different email.', 'error')
            # Close cursor and connection
            mycursor.close()
            db_connection.close()
            return redirect(url_for('create_account'))

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        account_type = request.form.get('account_type')

        sql = "INSERT INTO users (username, email, password, account_type) VALUES (%s, %s, %s, %s)"
        val = (username, email, hashed_password, account_type)
        mycursor.execute(sql, val)
        db_connection.commit()

        user_id = mycursor.lastrowid

        session['user_id'] = user_id
        if account_type == 'child':
            sql = "INSERT INTO wallets (user_id, current_amount) VALUES (%s, %s)"
            val = (user_id, 0)
            mycursor.execute(sql, val)
            db_connection.commit()

            sql = "INSERT INTO piggy_banks (user_id, current_amount) VALUES (%s, %s)"
            val = (user_id, 0)
            mycursor.execute(sql, val)
            db_connection.commit()


        # Close cursor and connection
        mycursor.close()
        db_connection.close()

        if account_type == 'parent':
            return redirect(url_for('connect_account'))
        else:
            return render_template('confirmation.html')
    else:
        return render_template('create_account.html')


def get_user_jars_from_database(user_id):
    """Function to fetch user jars from the database."""
    # Create database connection and cursor
    db_connection, cursor = create_db_connection()

    try:
        # Fetch user jars from the database
        cursor.execute("SELECT * FROM jars WHERE user_id = %s", (user_id,))
        user_jars = cursor.fetchall()
        return user_jars
    except mysql.connector.Error as err:
        print(f"Error fetching user jars: {err}")
        return []

    finally:
        # Close cursor and connection
        cursor.close()
        db_connection.close()

@app.route('/')
def main_page():
    return render_template('index.html')

@app.route('/connect_account', methods=['GET', 'POST'])
def connect_account():
    parent_id = session.get('user_id')
    print(parent_id)

    if request.method == 'POST':
        child_email = request.form['child_email']

        mycursor.execute("SELECT * FROM users WHERE email = %s", (child_email,))
        child_user = mycursor.fetchone()

        if child_user:
            mycursor.execute("UPDATE users SET parent_id = %s WHERE id = %s", (parent_id, child_user[0]))
            db_connection.commit()  # Changed to use db_connection instead of mydb

            return redirect(url_for('connection_success'))
        else:
            return render_template('child_not_found.html')
    else:
        return render_template('connect_account.html')



@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/connection_success')
def connection_success():
    parent_id = session.get('user_id')

    if parent_id:
        mycursor.execute("SELECT * FROM users WHERE parent_id = %s", (parent_id,))
        child_accounts = mycursor.fetchall()

        print("Child accounts:", child_accounts)

        return render_template('connection_success.html', child_accounts=child_accounts)
    else:
        flash('User ID not found in session. Please log in again.', 'error')
        return redirect(url_for('login'))


login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_id, email, username, account_type):
        self.id = user_id
        self.email = email
        self.username = username
        self.account_type = account_type


@login_manager.user_loader
def load_user(user_id):
    mycursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = mycursor.fetchone()
    if user_data:
        return User(user_data[0], user_data[2], user_data[1], user_data[4])
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Query the database to find the user with the given email
        mycursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = mycursor.fetchone()
        print(email, password)

        if user_data and bcrypt.checkpw(password.encode(), user_data[3].encode()):
            # If the user exists and the password is correct, create a User object
            user = User(user_data[0], user_data[2], user_data[1], user_data[4])

            # Update last login date in the database
            db_connection.commit()  # Changed to use db_connection instead of mydb

            # Store user information in session
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email
            session['account_type'] = user.account_type



            # Redirect based on the user's account type
            if user.account_type == 'parent':
                return redirect(url_for('parent_account'))
            elif user.account_type == 'child':
                return redirect(url_for('child_account'))
            else:
                return redirect(url_for('main_page'))  # Redirect to the main page or dashboard for other account types

        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/success')
@login_required
def success():
    user = User(session['_user_id'], '', '', '')
    return render_template('success.html', user=user)

@app.route('/child_account')
def child_account():
    user_id = session.get('user_id')

    if user_id:
        username = session.get('username')
        db_connection, mycursor = create_db_connection()

        try:
            # Fetch last_login_date from the database
            mycursor.execute("SELECT last_login FROM users WHERE id = %s", (user_id,))
            last_login_date_result = mycursor.fetchone()
            print(last_login_date_result)
            if last_login_date_result[0] is not None:
                last_login_date = last_login_date_result[0].date()  # Convert to datetime.date
            else:
                last_login_date = None

            # Fetch wallet current_amount
            mycursor.execute("SELECT current_amount FROM wallets WHERE user_id = %s", (user_id,))
            wallet_current_amount = mycursor.fetchone()[0]

            # Fetch piggy bank current_amount
            mycursor.execute("SELECT current_amount FROM piggy_banks WHERE user_id = %s", (user_id,))
            piggy_bank_current_amount = mycursor.fetchone()[0] or 0.0

            # Fetch jar data
            mycursor.execute("SELECT id, label, current_amount, target_amount FROM jars WHERE user_id = %s", (user_id,))
            jars = [{'id': row[0], 'label': row[1], 'current_amount': row[2], 'target_amount': row[3]} for row in
                    mycursor.fetchall()]

            # Fetch pocket money records
            mycursor.execute("""
                SELECT pocket_money_id, amount, frequency, day_of_month, day_of_week 
                FROM pocket_money 
                WHERE user_id = %s
            """, (user_id,))
            pocket_money_records = mycursor.fetchall()

            unclaimed_notifications = []
            notifications = []
            current_date = datetime.date.today()

            if not last_login_date:
                last_login_date = current_date

            day_of_week_mapping = {
                'Monday': 0,
                'Tuesday': 1,
                'Wednesday': 2,
                'Thursday': 3,
                'Friday': 4,
                'Saturday': 5,
                'Sunday': 6
            }

            if last_login_date != current_date:
                for record in pocket_money_records:
                    pocket_money_id, amount, frequency, day_of_month, day_of_week = record
                    days_since_last_login = (current_date - last_login_date).days

                    if frequency == 'daily':
                        for i in range(0, days_since_last_login):
                            notification_date = current_date - datetime.timedelta(days=i)
                            notification_message = f'Collect daily pocket money for {notification_date.strftime("%Y-%m-%d")}'
                            notification_date_str = notification_date.strftime("%Y-%m-%d")

                            mycursor.execute("""
                                SELECT COUNT(*) FROM notifications 
                                WHERE user_id = %s AND pocket_money_id = %s 
                                AND notification_message = %s AND pocket_money_date = %s
                            """, (user_id, pocket_money_id, notification_message, notification_date_str))

                            if mycursor.fetchone()[0] == 0:
                                notifications.append({
                                    'pocket_money_id': pocket_money_id,
                                    'message': notification_message,
                                    'pocket_money_date': notification_date_str
                                })

                    elif frequency == 'weekly':
                        target_day_of_week = day_of_week_mapping[day_of_week]
                        days_since_last_target_day = (current_date.weekday() - target_day_of_week) % 7
                        first_target_date = current_date - datetime.timedelta(days=days_since_last_target_day)

                        for i in range(0, days_since_last_login, 7):
                            notification_date = first_target_date - datetime.timedelta(weeks=i // 7)
                            if notification_date > last_login_date:
                                notification_message = f'Collect weekly pocket money for week of {notification_date.strftime("%Y-%m-%d")}'
                                notification_date_str = notification_date.strftime("%Y-%m-%d")

                                mycursor.execute("""
                                    SELECT COUNT(*) FROM notifications 
                                    WHERE user_id = %s AND pocket_money_id = %s 
                                    AND notification_message = %s AND pocket_money_date = %s
                                """, (user_id, pocket_money_id, notification_message, notification_date_str))

                                if mycursor.fetchone()[0] == 0:
                                    notifications.append({
                                        'pocket_money_id': pocket_money_id,
                                        'message': notification_message,
                                        'pocket_money_date': notification_date_str
                                    })

                    elif frequency == 'monthly':
                        months_since_last_login = (current_date.year - last_login_date.year) * 12 + current_date.month - last_login_date.month
                        for i in range(0, months_since_last_login):
                            notification_date = datetime.datetime(current_date.year, current_date.month, day_of_month) - datetime.timedelta(days=30 * i)

                            # Ensure the date is set to the 1st of the month if it's not
                            if notification_date.day != day_of_month:
                                notification_date = notification_date.replace(day=day_of_month)
                            notification_message = f'Collect monthly pocket money for {notification_date.strftime("%B")}'
                            notification_date_str = notification_date.strftime("%Y-%m-%d")

                            mycursor.execute("""
                                SELECT COUNT(*) FROM notifications 
                                WHERE user_id = %s AND pocket_money_id = %s 
                                AND notification_message = %s AND pocket_money_date = %s
                            """, (user_id, pocket_money_id, notification_message, notification_date_str))

                            if mycursor.fetchone()[0] == 0:
                                notifications.append({
                                    'pocket_money_id': pocket_money_id,
                                    'message': notification_message,
                                    'pocket_money_date': notification_date_str
                                })

                # Insert notifications into the database
                for notification in notifications:
                    mycursor.execute("""
                        INSERT INTO notifications (user_id, notification_message, pocket_money_date, pocket_money_id) 
                        VALUES (%s, %s, %s, %s)
                    """, (
                        user_id,
                        notification['message'],
                        notification['pocket_money_date'],
                        notification['pocket_money_id']
                    ))
                    db_connection.commit()

                # Update the last login date in the database
                mycursor.execute("""
                    UPDATE users 
                    SET last_login = %s 
                    WHERE id = %s
                """, (current_date.strftime('%Y-%m-%d %H:%M:%S'), user_id))
                db_connection.commit()

                # Update the session variables
                session['last_login_date'] = current_date.strftime('%Y-%m-%d %H:%M:%S')
                session['notifications_updated'] = True

                # Fetch unclaimed notifications
                mycursor.execute("""
                    SELECT notification_id, notification_message, pocket_money_id, pocket_money_date 
                    FROM notifications 
                    WHERE user_id = %s
                """, (user_id,))
                unclaimed_notifications = [
                    {'id': notification[0], 'message': notification[1], 'pocket_money_id': notification[2],
                     'pocket_money_date': notification[3]}
                    for notification in mycursor.fetchall()
                ]

            return render_template(
                'child_account.html',
                user={'id': user_id, 'username': username},
                wallet_current_amount=wallet_current_amount,
                piggy_bank_current_amount=piggy_bank_current_amount,
                jars=jars,
                last_login_date=last_login_date.strftime("%Y-%m-%d"),
                notifications=unclaimed_notifications
            )
        finally:
            mycursor.close()
            db_connection.close()
    else:
        flash('User is not logged in.', 'error')
        return redirect(url_for('login'))


@app.route('/transfer')
def transfer():
    user_id = session.get('user_id')
    amount = request.args.get('amount', type=float)
    from_account = request.args.get('from_account')
    to_account = request.args.get('to_account')
    from_id = request.args.get('from_id')
    to_id = request.args.get('to_id')

    if user_id and amount > 0 and from_account and to_account:
        db_connection, mycursor = create_db_connection()

        try:
            # Fetch current_amount from source account
            if from_account == 'jars':
                from_account_query = "SELECT current_amount FROM jars WHERE user_id = %s AND id = %s"
                mycursor.execute(from_account_query, (user_id, from_id))
            else:
                from_account_query = "SELECT current_amount FROM {} WHERE user_id = %s".format(from_account)
                mycursor.execute(from_account_query, (user_id,))

            from_current_amount = Decimal(mycursor.fetchone()[0])

            # Check if the source account has sufficient current_amount
            if from_current_amount >= Decimal(amount):
                # Update current_amount in source account
                new_from_current_amount = from_current_amount - Decimal(amount)

                if from_account == 'jars':
                    update_from_account_query = "UPDATE jars SET current_amount = %s WHERE user_id = %s AND id = %s"
                    mycursor.execute(update_from_account_query, (new_from_current_amount, user_id, from_id))
                else:
                    update_from_account_query = "UPDATE {} SET current_amount = %s WHERE user_id = %s".format(
                        from_account)
                    mycursor.execute(update_from_account_query, (new_from_current_amount, user_id))

                # Fetch current_amount from destination account
                if to_account == 'jars':
                    to_account_query = "SELECT current_amount FROM jars WHERE user_id = %s AND id = %s"
                    mycursor.execute(to_account_query, (user_id, to_id))
                else:
                    to_account_query = "SELECT current_amount FROM {} WHERE user_id = %s".format(to_account)
                    mycursor.execute(to_account_query, (user_id,))

                to_current_amount = Decimal(mycursor.fetchone()[0])

                # Update current_amount in destination account
                new_to_current_amount = to_current_amount + Decimal(amount)

                if to_account == 'jars':
                    update_to_account_query = "UPDATE jars SET current_amount = %s WHERE user_id = %s AND id = %s"
                    mycursor.execute(update_to_account_query, (new_to_current_amount, user_id, to_id))
                else:
                    update_to_account_query = "UPDATE {} SET current_amount = %s WHERE user_id = %s".format(to_account)
                    mycursor.execute(update_to_account_query, (new_to_current_amount, user_id))

                db_connection.commit()
                flash('Money transferred successfully!', 'success')
            else:
                flash('Insufficient current_amount in {}!'.format(from_account), 'error')

        except Exception as e:
            db_connection.rollback()
            flash(f'An error occurred: {str(e)}', 'error')

        finally:
            mycursor.close()
            db_connection.close()

    return redirect(url_for('child_account'))


@app.route('/claim_all', methods=['POST'])
def claim_all():
    user_id = session.get('user_id')

    if not user_id:
        flash('User is not logged in.', 'error')
        return redirect(url_for('login'))

    db_connection, mycursor = create_db_connection()

    try:
        total_to_claim = 0

        # Fetch unclaimed notifications
        mycursor.execute("""
            SELECT notification_id, pocket_money_id 
            FROM notifications 
            WHERE user_id = %s
        """, (user_id,))
        unclaimed_notifications = mycursor.fetchall()

        for notification in unclaimed_notifications:
            notification_id, pocket_money_id = notification

            # Retrieve allocations for user_id and pocket_money_id
            mycursor.execute(
                "SELECT jar_id, piggy_bank_id, wallet_id, amount FROM allocations WHERE user_id = %s AND pocket_money_id = %s",
                (user_id, pocket_money_id))
            allocations = mycursor.fetchall()
            print(f"Allocations for notification ID {notification_id}: {allocations}")

            if allocations:
                for allocation in allocations:
                    jar_id, piggy_bank_id, wallet_id, amount = allocation

                    if jar_id is not None:
                        # Update jars table
                        mycursor.execute("UPDATE jars SET current_amount = current_amount + %s WHERE id = %s", (amount, jar_id))
                        print(f"Updated jar {jar_id} by adding {amount}")

                    if piggy_bank_id is not None:
                        # Update piggy_banks table
                        mycursor.execute("UPDATE piggy_banks SET current_amount = current_amount + %s WHERE id = %s", (amount, piggy_bank_id))
                        print(f"Updated piggy bank {piggy_bank_id} by adding {amount}")

                    if wallet_id is not None:
                        # Update wallets table
                        mycursor.execute("UPDATE wallets SET current_amount = current_amount + %s WHERE id = %s", (amount, wallet_id))
                        print(f"Updated wallet {wallet_id} by adding {amount}")

                    total_to_claim += amount

            else:
                # No allocations found, add to wallet by default
                pocket_money_amount = get_pocket_money_amount(pocket_money_id)
                mycursor.execute("UPDATE wallets SET current_amount = current_amount + %s WHERE user_id = %s",
                                 (pocket_money_amount, user_id))
                print(f"No allocations found for notification ID {notification_id}, added {pocket_money_amount} to wallet.")

            # Delete the notification
            mycursor.execute("DELETE FROM notifications WHERE notification_id = %s AND user_id = %s", (notification_id, user_id))
            affected_rows = mycursor.rowcount
            print(f"Attempted to delete notification ID {notification_id} for user ID {user_id}, affected rows: {affected_rows}")

            if affected_rows == 0:
                print(f"No notification deleted. Either the notification ID {notification_id} does not exist or it does not belong to user ID {user_id}.")
                raise ValueError(f"Failed to delete notification ID {notification_id}")

        # Commit the transaction
        db_connection.commit()
        print(f"Transaction committed for claiming notifications")

        flash(f'You claimed a total of {total_to_claim} and it has been allocated to your jars, piggy banks, or wallet.', 'success')

    except Exception as e:
        # Rollback the transaction if an error occurs
        db_connection.rollback()
        flash('An error occurred while processing your claim. Please try again later.', 'error')
        print(f"Error: {e}")

    finally:
        # Close cursor and database connection
        mycursor.close()
        db_connection.close()
        print("Database connection closed")

        # Redirect back to the notifications page
        return redirect(url_for('notifications'))

@app.route('/notifications')
def notifications():
    user_id = session.get('user_id')
    last_login_date = session.get('last_login_date')

    if user_id:
        username = session.get('username')
        db_connection, mycursor = create_db_connection()

        # Fetch unclaimed notifications
        mycursor.execute("""
            SELECT notification_id, notification_message, pocket_money_id, pocket_money_date 
            FROM notifications 
            WHERE user_id = %s
        """, (user_id,))
        unclaimed_notifications = [
            {'id': notification[0], 'message': notification[1], 'pocket_money_id': notification[2],
             'pocket_money_date': notification[3]}
            for notification in mycursor.fetchall()
        ]

        # Calculate total to claim
        total_to_claim = sum(get_pocket_money_amount(notification['pocket_money_id']) for notification in unclaimed_notifications)


        mycursor.close()
        db_connection.close()

        return render_template(
            'notifications.html',
            user={'id': user_id, 'username': username},
            notifications=unclaimed_notifications,
            total_to_claim=total_to_claim
        )
    else:
        flash('User is not logged in.', 'error')
        return redirect(url_for('login'))

@app.route('/claim_notification/<int:notification_id>', methods=['POST'])
def claim_notification(notification_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('User is not logged in.', 'error')
        return redirect(url_for('login'))

    print(f"Claim notification called for user ID {user_id} and notification ID {notification_id}")

    try:
        # Establish a database connection and create a cursor
        db_connection, mycursor = create_db_connection()

        # Start a transaction
        db_connection.start_transaction()
        print("Transaction started")

        # Retrieve pocket money ID and amount
        mycursor.execute(
            "SELECT pocket_money_id FROM notifications WHERE notification_id = %s",
            (notification_id,))
        result = mycursor.fetchone()
        if not result:
            raise ValueError(f"No pocket money ID found for notification ID {notification_id}")

        pocket_money_id = result[0]
        print(f"Pocket Money ID: {pocket_money_id}")

        mycursor.execute(
            "SELECT amount FROM pocket_money WHERE pocket_money_id = %s",
            (pocket_money_id,))
        result = mycursor.fetchone()
        if not result:
            raise ValueError(f"No pocket money record found for pocket money ID {pocket_money_id}")

        pocket_money_amount = result[0]
        print(f"Pocket Money Amount: {pocket_money_amount}")

        # Retrieve allocations for user_id and pocket_money_id
        mycursor.execute(
            "SELECT jar_id, piggy_bank_id, wallet_id, amount FROM allocations WHERE user_id = %s AND pocket_money_id = %s",
            (user_id, pocket_money_id))
        allocations = mycursor.fetchall()
        print(f"Allocations: {allocations}")

        if allocations:
            for allocation in allocations:
                jar_id, piggy_bank_id, wallet_id, amount = allocation

                if jar_id is not None:
                    # Update jars table
                    mycursor.execute("UPDATE jars SET current_amount = current_amount + %s WHERE id = %s", (amount, jar_id))
                    print(f"Updated jar {jar_id} by adding {amount}")

                if piggy_bank_id is not None:
                    # Update piggy_banks table
                    mycursor.execute("UPDATE piggy_banks SET current_amount = current_amount + %s WHERE id = %s", (amount, piggy_bank_id))
                    print(f"Updated piggy bank {piggy_bank_id} by adding {amount}")

                if wallet_id is not None:
                    # Update wallets table
                    mycursor.execute("UPDATE wallets SET current_amount = current_amount + %s WHERE id = %s", (amount, wallet_id))
                    print(f"Updated wallet {wallet_id} by adding {amount}")

            # Delete the notification after processing all allocations
            mycursor.execute("DELETE FROM notifications WHERE notification_id = %s AND user_id = %s", (notification_id, user_id))
            affected_rows = mycursor.rowcount
            print(f"Attempted to delete notification ID {notification_id} for user ID {user_id}, affected rows: {affected_rows}")

            if affected_rows == 0:
                print(f"No notification deleted. Either the notification ID {notification_id} does not exist or it does not belong to user ID {user_id}.")
                raise ValueError(f"Failed to delete notification ID {notification_id}")
        else:
            # No allocations found, add the entire amount to the user's wallet
            mycursor.execute("UPDATE wallets SET current_amount = current_amount + %s WHERE user_id = %s", (pocket_money_amount, user_id))
            print(f"No allocations found, added {pocket_money_amount} to the user's wallet")

            # Delete the notification
            mycursor.execute("DELETE FROM notifications WHERE notification_id = %s AND user_id = %s", (notification_id, user_id))
            affected_rows = mycursor.rowcount
            print(f"Attempted to delete notification ID {notification_id} for user ID {user_id}, affected rows: {affected_rows}")

            if affected_rows == 0:
                print(f"No notification deleted. Either the notification ID {notification_id} does not exist or it does not belong to user ID {user_id}.")
                raise ValueError(f"Failed to delete notification ID {notification_id}")

        # Commit the transaction
        db_connection.commit()
        print(f"Transaction committed for claiming notification ID {notification_id}")

        flash(f'You claimed {pocket_money_amount} and it has been added to your jars, piggy banks, or wallet.', 'success')

    except Exception as e:
        # Rollback the transaction if an error occurs
        db_connection.rollback()
        flash('An error occurred while processing your claim. Please try again later.', 'error')
        print(f"Error: {e}")

    finally:
        # Close cursor and database connection
        mycursor.close()
        db_connection.close()
        print("Database connection closed")

        # Redirect back to the notifications page
        return redirect(url_for('notifications'))

    return render_template('child_account.html')



@app.route('/parent_account')
def parent_account():
    return 'Welcome to the Parent Account Page'

@app.route('/admin_account')
def admin_account():
    return 'Welcome to the Admin Account Page'



@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    return redirect(url_for('main_page'))

@app.route('/create_admin')
def create_admin():
    mycursor.execute("SELECT * FROM users WHERE account_type = 'admin'")
    admin_exists = mycursor.fetchone()

    if not admin_exists:
        admin_username = 'admin'
        admin_email = 'admin@example.com'
        admin_password = 'admin_password'
        hashed_password = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt())

        sql = "INSERT INTO users (username, email, password, account_type) VALUES (%s, %s, %s, %s)"
        val = (admin_username, admin_email, hashed_password, 'admin')
        mycursor.execute(sql, val)
        db_connection.commit()  # Changed to use db_connection instead of mydb

        flash('Admin account created successfully.', 'success')
    else:
        flash('Admin account already exists.', 'info')

    return redirect(url_for('main_page'))


@app.route('/create_category', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        category_name = request.form['category_name'].capitalize()
        user_id = session.get('user_id')

        if category_name.strip() != '':
            mycursor.execute("SELECT * FROM categories WHERE name = %s", (category_name,))
            existing_category = mycursor.fetchone()
            if existing_category:
                flash('Category already exists!', 'error')
            else:
                sql = "INSERT INTO categories (name) VALUES (%s)"
                val = (category_name,)
                mycursor.execute(sql, val)
                db_connection.commit()  # Changed to use db_connection instead of mydb

                category_id = mycursor.lastrowid

                sql = "INSERT INTO user_category (user_id, category_id) VALUES (%s, %s)"
                val = (user_id, category_id)
                mycursor.execute(sql, val)
                db_connection.commit()  # Changed to use db_connection instead of mydb

                flash('Category created successfully!', 'success')
                return redirect(url_for('create_category'))
        else:
            flash('Category name cannot be empty!', 'error')

    return render_template('create_category.html')


@app.route('/add_money', methods=['GET', 'POST'])
def add_money():
    user_id = session.get('user_id')
    if request.method == 'POST':
        amount = request.form['amount']
        description = request.form['description']
        print("User ID:", user_id)
        try:
            amount = float(amount)
        except ValueError:
            flash('Invalid amount entered!', 'error')
            return redirect(url_for('add_money'))

        print("User ID:", user_id)

        sql = "UPDATE wallets SET current_amount = current_amount + %s WHERE user_id = %s"
        val = (amount, user_id)

        print("SQL Query:", sql)
        print("Values:", val)
        mycursor.execute(sql, val)
        db_connection.commit()  # Changed to use db_connection instead of mydb

        flash('Money added successfully!', 'success')

        return render_template('add_money.html', user_id=user_id)

    return render_template('add_money.html', user_id=user_id)



@app.route('/add_spending/', methods=['GET', 'POST'])
def add_spending():
    user_id = session.get('user_id')
    if request.method == 'POST':
        amount = request.form['amount']
        category_id = request.form['category']
        description = request.form['description']
        print("User ID:", user_id)
        try:
            amount = float(amount)
        except ValueError:
            flash('Invalid amount entered!', 'error')
            return redirect(url_for('add_spending'))

        print("User ID:", user_id)

        sql = "INSERT INTO spendings (user_id, amount, category_id, date, time, description) VALUES (%s, %s, %s, CURDATE(), CURTIME(), %s)"
        val = (user_id, amount, category_id, description)
        mycursor.execute(sql, val)

        sql = "UPDATE wallets SET current_amount = current_amount - %s WHERE user_id = %s"
        val = (amount, user_id)
        print("SQL Query:", sql)
        print("Values:", val)
        mycursor.execute(sql, val)
        db_connection.commit()  # Changed to use db_connection instead of mydb

        flash('Spending added successfully!', 'success')
        last_spendings = get_last_spendings(user_id, limit=5)

        mycursor.execute("SELECT id, name FROM categories")
        categories = mycursor.fetchall()

        return render_template('add_spending.html', user_id=user_id, categories=categories, last_spendings=last_spendings)

    mycursor.execute("SELECT id, name FROM categories")
    categories = mycursor.fetchall()
    last_spendings = get_last_spendings(user_id, limit=5)
    return render_template('add_spending.html', user_id=user_id, categories=categories, last_spendings=last_spendings)


@app.route('/create_jar', methods=['GET', 'POST'])
def create_jar():
    user_id = session.get('user_id')
    if request.method == 'POST':
        label = request.form['label'].capitalize()
        target_amount = request.form['target_amount']

        if label.strip() != '':
            db_connection, mycursor = create_db_connection()
            mycursor.execute("SELECT * FROM jars WHERE label = %s AND user_id = %s", (label, user_id))
            existing_jar = mycursor.fetchone()
            if existing_jar:
                flash('Jar already exists!', 'error')
            else:
                sql = "INSERT INTO jars (label, target_amount, user_id) VALUES (%s, %s, %s)"
                val = (label, target_amount, user_id)
                mycursor.execute(sql, val)
                db_connection.commit()

                flash('Jar created successfully!', 'success')
                return redirect(url_for('create_jar'))
        else:
            flash('Label cannot be empty!', 'error')

    # Fetch user's jars from the database
    user_jars = get_user_jars_from_database(user_id=user_id)

    return render_template('create_jar.html', user_jars=user_jars, user_id=user_id)


@app.route('/settings_child', methods=['GET', 'POST'])
def settings_child():
    user_id = session.get('user_id')
    return render_template('settings_child.html', user_id=user_id)


from flask import request, redirect, url_for


@app.route('/pocket_money', methods=['GET', 'POST'])
def pocket_money():
    user_id = session.get('user_id')

    if request.method == 'POST':
        amount = request.form.get('amount')
        session['amount'] = amount  # Store amount in session
        print("amount", session['amount'])
        return redirect(url_for('pocket_money_frequency'))

    if user_id:
        db_connection, cursor = create_db_connection()

        try:
            # Fetch existing pocket money settings for the user for daily, weekly, and monthly frequencies
            daily_pocket_money = get_pocket_money_by_frequency(user_id, 'daily', cursor)
            weekly_pocket_money = get_pocket_money_by_frequency(user_id, 'weekly', cursor)
            monthly_pocket_money = get_pocket_money_by_frequency(user_id, 'monthly', cursor)

            # Handle the result if it's None
            if daily_pocket_money is None:
                daily_pocket_money = []
            if weekly_pocket_money is None:
                weekly_pocket_money = []
            if monthly_pocket_money is None:
                monthly_pocket_money = []

            return render_template('pocket_money.html', daily_pocket_money=daily_pocket_money, weekly_pocket_money=weekly_pocket_money, monthly_pocket_money=monthly_pocket_money)

        except Exception as e:
            print(f"Error fetching pocket money: {e}")
            return "An error occurred while fetching pocket money records.", 500

        finally:
            cursor.close()
            db_connection.close()
    else:
        return redirect(url_for('login'))

@app.route('/change_password', methods=['GET'])
def change_password():
    # Your change password logic here
    return render_template('change_password.html')

@app.route('/change_username', methods=['GET'])
def change_username():
    # Your change username logic here
    return render_template('change_username.html')

@app.route('/disconnect_from_parents_account', methods=['GET'])
def disconnect_from_parents_account():
    # Your disconnect from parent's account logic here
    return render_template('disconnect_from_parents_account.html')



@app.route('/delete_account', methods=['GET'])
def delete_account():
    # Your delete account logic here
    return render_template('delete_account.html')





@app.route('/pocket_money_frequency', methods=['GET', 'POST'])
def pocket_money_frequency():
    if request.method == 'POST':
        frequency = request.form.get('frequency')
        session['frequency'] = frequency  # Store frequency in session

        if frequency == 'weekly':
            print("weekly")
            return redirect(url_for('specify_day_of_week'))
        elif frequency == 'monthly':
            return redirect(url_for('specify_day_of_month'))
        else:
            session['day_of_month'] = None
            session['day_of_week'] = None
            return redirect(url_for('pocket_money_success'))

    return render_template('pocket_money_frequency.html')


@app.route('/specify_day_of_week', methods=['GET', 'POST'])
def specify_day_of_week():
    print("start")
    if request.method == 'POST':
        day_of_week = request.form.get('dayOfWeek')
        session['day_of_week'] = day_of_week
        print("dayofweek")
        return redirect(url_for('pocket_money_success'))
    print("stop")
    return render_template('specify_day_of_week.html')


@app.route('/specify_day_of_month', methods=['GET', 'POST'])
def specify_day_of_month():
    print("start")
    if request.method == 'POST':
        day_of_week = request.form.get('dayOfMonth')
        session['day_of_month'] = day_of_week
        print("dayofweek")
        return redirect(url_for('pocket_money_success'))
    print("stop")
    return render_template('specify_day_of_month.html')


@app.route('/pocket_money_success', methods=['GET', 'POST'])
def pocket_money_success():
    user_id = session.get('user_id')
    amount = session.get('amount')
    frequency = session.get('frequency')
    day_of_month = session.get('day_of_month')
    day_of_week = session.get('day_of_week')
    print("success")

    # Insert data into the pocket_money table
    sql = "INSERT INTO pocket_money (user_id, amount, frequency, day_of_month, day_of_week) VALUES (%s, %s, %s, %s, %s)"
    val = (user_id, amount, frequency, day_of_month, day_of_week)

    # Get a new database connection and cursor
    connection, cursor = create_db_connection()
    try:
        cursor.execute(sql, val)
        connection.commit()
        flash('Pocket money settings added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'error')
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('pocket_money_message'))  # Redirect to pocket_money_message route after success
@app.route('/pocket_money_message', methods=['GET', 'POST'])
def pocket_money_message():
    return render_template('pocket_money_message.html')


@app.route('/edit_pocket_money/<int:record_id>', methods=['GET', 'POST'])
def edit_pocket_money(record_id):
    user_id = session.get('user_id')
    connection, cursor = create_db_connection()

    try:
        # Fetching pocket money records based on frequency
        daily_pocket_money = get_pocket_money_by_frequency(user_id, 'daily', cursor)
        weekly_pocket_money = get_pocket_money_by_frequency(user_id, 'weekly', cursor)
        monthly_pocket_money = get_pocket_money_by_frequency(user_id, 'monthly', cursor)

        if request.method == 'POST':
            # Handle form submission to update the record in the database
            # Retrieve form data
            amount = request.form.get('amount')
            frequency = request.form.get('frequency')
            day_of_month = request.form.get('day_of_month')
            day_of_week = request.form.get('day_of_week')

            # Update the record in the database
            sql = "UPDATE pocket_money SET amount = %s, frequency = %s, day_of_month = %s, day_of_week = %s WHERE pocket_money_id = %s AND user_id = %s"
            val = (amount, frequency, day_of_month, day_of_week, record_id, user_id)
            cursor.execute(sql, val)
            connection.commit()

            flash('Pocket money record updated successfully!', 'success')

            # Redirect back to the pocket money settings page with the currently edited record
            return redirect(url_for('edit_pocket_money', record_id=record_id))

        else:
            # Fetch the record from the database and pre-fill the form fields with its data
            sql = "SELECT * FROM pocket_money WHERE pocket_money_id = %s AND user_id = %s"
            val = (record_id, user_id)
            cursor.execute(sql, val)
            record = cursor.fetchone()

            if record:
                # Pass the record data and fetched pocket money records to the template
                return render_template('edit_pocket_money.html', record=record, record_id=record_id,
                                       daily_pocket_money=daily_pocket_money,
                                       weekly_pocket_money=weekly_pocket_money,
                                       monthly_pocket_money=monthly_pocket_money)
            else:
                flash('Pocket money record not found!', 'error')
                return redirect(url_for('pocket_money'))

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'error')

    finally:
        cursor.close()
        connection.close()


@app.route('/delete_pocket_money', methods=['POST'])
def delete_pocket_money():
    user_id = session.get('user_id')
    record_id = request.args.get('record_id')

    if request.method == 'POST':
        # Get a new database connection and cursor
        connection, cursor = create_db_connection()

        try:
            sql = "DELETE FROM pocket_money WHERE user_id = %s AND pocket_money_id = %s"
            val = (user_id, record_id)
            cursor.execute(sql, val)
            connection.commit()
            flash('Record deleted successfully!', 'success')
        except Exception as e:
            print("Error:", e)
            connection.rollback()
            flash('An error occurred while deleting the record.', 'error')
        finally:
            cursor.close()
            connection.close()

    return redirect(url_for('pocket_money'))


@app.route('/edit_frequency/<int:record_id>', methods=['GET', 'POST'])
def edit_frequency(record_id):
    user_id = session.get('user_id')

    # Get a new database connection and cursor
    connection, cursor = create_db_connection()

    if request.method == 'POST':
        frequency = request.form.get('frequency')

        try:
            # Update the frequency in the database
            sql = "UPDATE pocket_money SET frequency = %s WHERE pocket_money_id = %s AND user_id = %s"
            val = (frequency, record_id, user_id)
            cursor.execute(sql, val)
            connection.commit()
        except Exception as e:
            print("Error:", e)
            connection.rollback()
            flash('An error occurred while updating the record.', 'error')
        finally:
            cursor.close()
            connection.close()

        # Redirect the user to the appropriate page based on the new frequency
        if frequency == 'weekly':
            return redirect(url_for('edit_day_of_week', record_id=record_id))
        elif frequency == 'monthly':
            return redirect(url_for('edit_day_of_month', record_id=record_id))
        else:
            # Redirect to the pocket money settings page if frequency is not weekly or monthly
            return redirect(url_for('pocket_money'))

    else:
        try:
            # Fetch the entire record from the database to display its current frequency
            sql = "SELECT * FROM pocket_money WHERE pocket_money_id = %s AND user_id = %s"
            val = (record_id, user_id)
            cursor.execute(sql, val)
            record = cursor.fetchone()
        except Exception as e:
            print("Error:", e)
            flash('An error occurred while fetching the record.', 'error')
            return redirect(url_for('pocket_money'))
        finally:
            cursor.close()
            connection.close()

        if record:
            return render_template('edit_frequency.html', record=record)
        else:
            flash('Pocket money record not found!', 'error')
            return redirect(url_for('pocket_money'))


@app.route('/choose_day_of_week/<int:record_id>', methods=['GET', 'POST'])
def choose_day_of_week(record_id):
    # Logic to choose day of the week
    pass


@app.route('/edit_amount/<int:record_id>', methods=['GET', 'POST'])
def edit_amount(record_id):
    user_id = session.get('user_id')

    # Get a new database connection and cursor
    connection, cursor = create_db_connection()

    if request.method == 'POST':
        try:
            # Handle form submission to update the amount in the database
            amount = request.form.get('amount')

            # Update the record in the database
            sql = "UPDATE pocket_money SET amount = %s WHERE pocket_money_id = %s AND user_id = %s"
            val = (amount, record_id, user_id)
            cursor.execute(sql, val)
            connection.commit()

            flash('Amount updated successfully!', 'success')

            # Redirect back to the edit pocket money page
            return redirect(url_for('edit_pocket_money', record_id=record_id))
        except Exception as e:
            print("Error:", e)
            connection.rollback()
            flash('An error occurred while updating the amount.', 'error')
        finally:
            cursor.close()
            connection.close()

    else:
        try:
            # Fetch the record from the database and pre-fill the form field with its data
            sql = "SELECT amount FROM pocket_money WHERE pocket_money_id = %s AND user_id = %s"
            val = (record_id, user_id)
            cursor.execute(sql, val)
            record = cursor.fetchone()
        except Exception as e:
            print("Error:", e)
            flash('An error occurred while fetching the record.', 'error')
            return redirect(url_for('pocket_money'))
        finally:
            cursor.close()
            connection.close()

        if record:
            # Pass the record data to the template
            return render_template('edit_amount.html', record=record, record_id=record_id)
        else:
            flash('Pocket money record not found!', 'error')
            return redirect(url_for('pocket_money'))


@app.route('/edit_day_of_month/<int:record_id>', methods=['GET', 'POST'])
def edit_day_of_month(record_id):
    user_id = session.get('user_id')

    # Get a new database connection and cursor
    connection, cursor = create_db_connection()

    if request.method == 'POST':
        try:
            # Handle form submission to update the day of the month in the database
            new_day_of_month = request.form.get('day_of_month')

            # Validate the input
            try:
                new_day_of_month = int(new_day_of_month)
                if new_day_of_month < 1 or new_day_of_month > 28:
                    raise ValueError("Day of month must be between 1 and 28")
            except ValueError:
                flash('Invalid input for day of month! Please enter a number between 1 and 28.', 'error')
                return redirect(url_for('edit_day_of_month', record_id=record_id))

            # Update the day of the month for the specified record in the database
            sql = "UPDATE pocket_money SET day_of_month = %s WHERE pocket_money_id = %s AND user_id = %s"
            val = (new_day_of_month, record_id, user_id)
            cursor.execute(sql, val)
            connection.commit()

            flash('Day of month updated successfully!', 'success')

            # Redirect back to the pocket money settings page with the currently edited record
            return redirect(url_for('edit_pocket_money', record_id=record_id))
        except Exception as e:
            print("Error:", e)
            connection.rollback()
            flash('An error occurred while updating the day of month.', 'error')
        finally:
            cursor.close()
            connection.close()

    else:
        try:
            # Fetch the record from the database to display its current day of the month
            sql = "SELECT day_of_month FROM pocket_money WHERE pocket_money_id = %s AND user_id = %s"
            val = (record_id, user_id)
            cursor.execute(sql, val)
            record = cursor.fetchone()
        except Exception as e:
            print("Error:", e)
            flash('An error occurred while fetching the record.', 'error')
            return redirect(url_for('pocket_money'))
        finally:
            cursor.close()
            connection.close()

        if record:
            # Pass the record data to the template
            return render_template('edit_day_of_month.html', record=record, record_id=record_id)
        else:
            flash('Pocket money record not found!', 'error')
            return redirect(url_for('pocket_money'))


@app.route('/edit_day_of_week/<int:record_id>', methods=['GET', 'POST'])
def edit_day_of_week(record_id):
    user_id = session.get('user_id')

    # Get a new database connection and cursor
    connection, cursor = create_db_connection()

    if request.method == 'POST':
        print("HHHHH")
        try:
            print("HHHHH")
            # Handle form submission to update the day of the week in the database
            new_day_of_week = request.form.get('day_of_week')

            # Update the day of the week for the specified record in the database
            sql = "UPDATE pocket_money SET day_of_week = %s WHERE pocket_money_id = %s AND user_id = %s"
            val = (new_day_of_week, record_id, user_id)
            cursor.execute(sql, val)
            connection.commit()

            flash('Day of week updated successfully!', 'success')

            # Redirect back to the pocket money settings page with the currently edited record
            return redirect(url_for('edit_pocket_money', record_id=record_id))
        except Exception as e:
            print("Error:", e)
            connection.rollback()
            flash('An error occurred while updating the day of week.', 'error')
        finally:
            cursor.close()
            connection.close()

    else:
        try:
            # Fetch the record from the database to display its current day of the week
            sql = "SELECT day_of_week FROM pocket_money WHERE pocket_money_id = %s AND user_id = %s"
            val = (record_id, user_id)
            cursor.execute(sql, val)
            record = cursor.fetchone()
        except Exception as e:
            print("Error:", e)
            flash('An error occurred while fetching the record.', 'error')
            return redirect(url_for('pocket_money'))
        finally:
            cursor.close()
            connection.close()

        if record:
            # Pass the record data to the template
            return render_template('edit_day_of_week.html', record=record, record_id=record_id)
        else:
            flash('Pocket money record not found!', 'error')
            return redirect(url_for('pocket_money'))


@app.route('/manage_pocket_money/<int:record_id>', methods=['GET', 'POST'])
def manage_pocket_money(record_id):
    user_id = session.get('user_id')
    pocket_money_amount = get_pocket_money_amount(record_id)
    jars = get_user_jars_from_database(user_id)

    if request.method == 'POST':
        try:
            # Validate if the total entered amounts match pocket money amount
            total_entered_amount = 0

            # Sum up jar amounts
            for jar in jars:
                jar_id = jar[0]  # Assuming the first element is the id
                jar_value = float(request.form.get(f'jar{jar_id}', 0))
                total_entered_amount += jar_value

            # Add wallet amount
            wallet_amount = float(request.form.get('wallet_amount', 0))
            total_entered_amount += wallet_amount

            # Add piggy bank amount (assuming it's the savings_amount)
            piggy_bank_amount = float(request.form.get('savings_amount', 0))
            total_entered_amount += piggy_bank_amount

            if total_entered_amount != pocket_money_amount:
                flash('Entered amounts do not add up to pocket money amount!', 'error')
                return redirect(url_for('manage_pocket_money', record_id=record_id))

            # Insert jar values into allocations table
            for jar in jars:
                jar_id = jar[0]  # Assuming the first element is the id
                jar_value = float(request.form.get(f'jar{jar_id}', 0))
                sql = "INSERT INTO allocations (pocket_money_id, jar_id, amount, user_id) VALUES (%s, %s, %s, %s)"
                val = (record_id, jar_id, jar_value, user_id)
                mycursor.execute(sql, val)
                db_connection.commit()

            # Insert wallet amount into allocations table
            wallet_id = get_wallet_id(user_id)
            print("YYYYYYYYYYYYYY")
            print(record_id, wallet_amount, user_id, wallet_id)
            sql = "INSERT INTO allocations (pocket_money_id, amount, user_id, wallet_id) VALUES (%s, %s, %s, %s)"
            val = (record_id, wallet_amount, user_id, wallet_id)
            mycursor.execute(sql, val)
            db_connection.commit()

            # Insert piggy bank amount into allocations table
            piggy_bank_id = get_piggy_bank_id(user_id)  # Replace with your logic to get piggy_bank_id
            sql = "INSERT INTO allocations (pocket_money_id, amount, user_id, piggy_bank_id) VALUES (%s, %s, %s, %s)"
            val = (record_id, piggy_bank_amount, user_id, piggy_bank_id)
            mycursor.execute(sql, val)
            db_connection.commit()

            flash('Form submitted successfully!', 'success')
            return redirect(url_for('manage_pocket_money', record_id=record_id))

        except Exception as e:
            flash(f'Error occurred: {str(e)}', 'error')

    # If GET request or if there's an error, render the template with current data
    return render_template('manage_pocket_money.html',
                           record_id=record_id,
                           pocket_money_amount=pocket_money_amount,
                           jars=jars)


@app.route('/see_allocations/<int:record_id>', methods=['GET'])
def see_allocations(record_id):
    # Ensure the user is authenticated or authorized as needed
    # Example check: Check session, cookies, or any other authentication mechanism

    # Create a database connection and cursor
    db_connection, cursor = create_db_connection()

    try:
        # Fetch allocations based on the provided record_id
        allocations = get_allocations_by_record_id(record_id, cursor)

        # Process allocations to create table_data
        table_data = []
        if allocations:
            for allocation in allocations:
                if allocation[0] is not None:
                    table_data.append(('Jar', allocation[3]))
                if allocation[1] is not None:
                    table_data.append(('Piggy Bank', allocation[3]))
                if allocation[2] is not None:
                    table_data.append(('Wallet', allocation[3]))
        else:
            allocations = []
        return render_template('see_allocations.html', table_data=table_data, record_id=record_id)

    except Exception as e:
        print(f"Error fetching allocations: {e}")
        return "An error occurred while fetching allocations.", 500

    finally:
        cursor.close()
        db_connection.close()

@app.route('/delete_allocations/<int:record_id>', methods=['POST'])
def delete_allocations(record_id):
    # Ensure the user is authenticated or authorized as needed
    # Example check: Check session, cookies, or any other authentication mechanism

    # Create a database connection and cursor
    db_connection, cursor = create_db_connection()

    try:
        # Delete all allocations with the given pocket_money_id
        delete_query = "DELETE FROM allocations WHERE pocket_money_id = %s"
        cursor.execute(delete_query, (record_id,))
        db_connection.commit()

        return redirect(url_for('see_allocations', record_id=record_id))

    except Exception as e:
        print(f"Error deleting allocations: {e}")
        return "An error occurred while deleting the allocations.", 500

    finally:
        cursor.close()
        db_connection.close()

@app.route('/button')
def button():

        return render_template('button.html')


#
# @app.route('/manage_pocket_money/<int:record_id>', methods=['GET', 'POST'])
# def manage_pocket_money(record_id):
#     user_id = session.get('user_id')
#     if not user_id:
#         flash('User not logged in.', 'error')
#         return redirect(url_for('login'))
#
#     db_connection, mycursor = create_db_connection()
#
#     try:
#         if request.method == 'POST':
#             print("AAAAAAAAABBB")
#             # Handle form submission to save allocation preferences
#             savings_amount = float(request.form.get('savings_amount', 0))
#             jar_amount = float(request.form.get('jar_amount', 0))
#             wallet_amount = float(request.form.get('wallet_amount', 0))
#             pocket_money_amount = float(request.form.get('pocket_money_amount', 0))
#             jars = get_user_jars_from_database(user_id)
#             print("jars ", jars)
#             # Check if the sum of allocated amounts equals the pocket money amount
#             if (savings_amount + jar_amount + wallet_amount) == pocket_money_amount:
#                 # Save or update the user's allocation preferences in the database
#                 # Example: INSERT INTO allocation_preferences (user_id, destination, amount) VALUES (user_id, 'savings', savings_amount)
#                 # Similar for 'jar' and 'wallet'
#                 flash('Allocation preferences saved successfully!', 'success')
#                 return redirect(url_for('settings'))
#             else:
#                 flash('Allocated amounts do not add up to the pocket money amount.', 'error')
#                 # Fetch the amount of pocket money to be allocated
#                 pocket_money_amount = get_pocket_money_amount(record_id)
#
#                 return render_template('manage_pocket_money.html', record_id=record_id, savings_amount=savings_amount, jar_amount=jar_amount,
#                                         wallet_amount=wallet_amount, pocket_money_amount=pocket_money_amount, jars=jars)
#
#         else:
#             print("CCCCCCCCCCCCCC")
#             # Fetch the user's allocation preferences from the database
#             # Example: SELECT destination, amount FROM allocation_preferences WHERE user_id = user_id
#             # Placeholder, replace with actual database fetch
#
#             jars = get_user_jars_from_database(user_id)
#             # Fetch the amount of pocket money to be allocated
#             pocket_money_amount = get_pocket_money_amount(record_id)
#             print("DDDDDDDDDD")
#             print(pocket_money_amount)
#             print(jars)
#             print(record_id)
#             return render_template('manage_pocket_money.html', record_id=record_id, pocket_money_amount=pocket_money_amount, jars=jars)
#
#     except Exception as e:
#         flash(f'Error: {str(e)}', 'error')
#
#     finally:
#         mycursor.close()
#         db_connection.close()
#
#     return redirect(url_for('pocket_money'))
#

if __name__ == '__main__':
    app.run(debug=True)

#PREZKA