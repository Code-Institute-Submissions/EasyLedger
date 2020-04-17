import os
import pymongo
import pygal
import datetime
from flask import Flask, render_template, redirect, request, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from bson import json_util

from os import path
if path.exists('env.py'):
    import env

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'database'
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')

mongo = PyMongo(app)


"""--------------------------------Loads the Bar chart with Pygal--------------------------------"""
def bar_chart():
    credit_data = list(mongo.db.transactions.aggregate([
        {'$match': {'transition': 'credit'}},
        {'$group': {'_id': '$category_name', 'subtotal': {'$sum': '$amount'}}}
    ]))

    chart = pygal.Bar()
    credit_subtotals = [record['subtotal'] for record in credit_data]

    chart.x_labels = [record['_id'] for record in credit_data]
    chart.add('credit', credit_subtotals)
    chart_data = chart.render_data_uri()

    return chart_data


"""--------------------------------Loads the Pie chart with Pygal--------------------------------"""
def pie_chart():
    chart = pygal.Pie(inner_radius=.4)
    chart.add('Credit', credit_total())
    chart.add('Debit', debit_total())
    chart_data = chart.render_data_uri()

    return chart_data


"""--------------------------------------Loads the dashboard-------------------------------------"""
@app.route('/')
@app.route('/get_dashboard')
def get_dashboard():
    return render_template('dashboard.html',
                           debit=debit_total(),
                           credit=credit_total(),
                           total=grand_total(),
                           bar_chart=bar_chart(),
                           pie_chart=pie_chart())


"""----------------------------------Loads the Transactions page---------------------------------"""
@app.route('/get_transactions')
def get_transactions():
    return render_template('transactions.html',
                           transactions=mongo.db.transactions.find(),
                           categories=mongo.db.categories.find(),
                           debit=debit_total(),
                           credit=credit_total(),
                           total=grand_total())


"""----------------------Calculates the total of all the DEBIT transactions----------------------"""
def debit_total():
    transaction_amount = []

    for record in mongo.db.transactions.find({'transition': 'debit'}):
        transaction_amount.append(float(record['amount']))

    return sum(transaction_amount)


"""----------------------Calculates the total of all the CREDIT transactions---------------------"""
def credit_total():
    transaction_amount = []

    for record in mongo.db.transactions.find({'transition': 'credit'}):
        transaction_amount.append(float(record['amount']))

    return sum(transaction_amount)


"""----------------------Calculates the GRAND total of all the transactions----------------------"""
def grand_total():
    calc = debit_total() - credit_total()

    return calc


"""-------------------------------------Creates a transaction------------------------------------"""
@app.route('/insert_transaction', methods=['POST'])
def insert_transaction():
    transactions = mongo.db.transactions
    transactions.insert_one({'transition': request.form.get('transition'),
                             'category_name': request.form.get('category_name'),
                             'details': request.form.get('details'),
                             'date': datetime.datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M:%S.000Z'),
                             'amount': float(request.form.get('amount'))})

    return redirect(url_for('get_transactions'))


"""-------------------------------------Loads the edit transaction------------------------------------"""
@app.route('/edit_transaction/<transaction_id>')
def edit_transaction(transaction_id):
    the_transaction = mongo.db.transactions.find_one(
        {'_id': ObjectId(transaction_id)})
    all_categories = mongo.db.categories.find()

    return render_template('edittransaction.html',
                           transaction=the_transaction,
                           categories=all_categories)


"""-------------------------------------Updates a transaction------------------------------------"""
@app.route('/update_transaction/<transaction_id>', methods=['POST'])
def update_transaction(transaction_id):
    transactions = mongo.db.transactions
    transactions.update({'_id': ObjectId(transaction_id)},
                        {'transition': request.form.get('transition'),
                         'category_name': request.form.get('category_name'),
                         'details': request.form.get('details'),
                         'date': request.form.get('date'),
                         'amount': request.form.get('amount')})

    return redirect(url_for('get_transactions'))


"""-------------------------Deletes a transaction by searching on it's id------------------------"""
@app.route('/delete_transaction/<transaction_id>')
def delete_transaction(transaction_id):
    mongo.db.transactions.remove({'_id': ObjectId(transaction_id)})

    return redirect(url_for('get_transactions'))


"""---------------------------Run the app and set the proper IP + Port---------------------------"""
if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)
