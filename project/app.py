import os
from difflib import SequenceMatcher
from flask import Flask, render_template, request
import csv
import random
from flask_paginate import Pagination, get_page_args
from requests import Session

app = Flask(__name__)

# Function to load data from CSV files into a list of dictionaries and shuffle it
def load_data():
    data = []
    # Add more CSV files here if needed
    csv_files = ['Flipkart.csv', 'amazon_products.csv','Reliance1.csv']
    for file_name in csv_files:
        csv_path = os.path.join(os.path.dirname(__file__), 'csv_files', file_name)
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data.append(row)
    # Shuffle the data
    return data
def is_similar(name1, name2):
    # Split names into first word and remaining part
    name1_parts = name1.split(maxsplit=1)
    name2_parts = name2.split(maxsplit=1)

    # Check if the first word matches exactly
    first_word_match = name1_parts[0].lower() == name2_parts[0].lower()

    # Check if the remaining part matches with a lower threshold
    remaining_similarity = 0.0
    if len(name1_parts) > 1 and len(name2_parts) > 1:
        remaining_similarity = SequenceMatcher(None, name1_parts[1], name2_parts[1]).ratio()

    return first_word_match, remaining_similarity

# Function to get the paginated results
def get_paginated_results(data, page, per_page):
    offset = (page - 1) * per_page
    return data[offset: offset + per_page]

# Homepage
@app.route('/')
def index():
    search_results = []
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    pagination = Pagination(page=page, per_page=per_page, total=0, css_framework='bootstrap4')
    return render_template('index.html', search_results=search_results, pagination=pagination)

# Category page
@app.route('/category/<category_name>')
def category(category_name):
    products = []
    csv_files = [ 'Flipkart.csv','amazon_products.csv','Reliance1.csv']
    for file_name in csv_files:
        csv_path = os.path.join(os.path.dirname(__file__), 'csv_files', file_name)
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            data = [row for row in csv_reader if category_name.lower() in row['main_category'].lower()]
            products.extend(data[:30])  # Get 20 products from each CSV
    random.shuffle(products)
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(products)
    pagination_products = get_paginated_results(products, page, per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
    return render_template('category.html', products=pagination_products, category_name=category_name, pagination=pagination)

#search functionality
@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.form.get('search_query', '').lower()
    all_data = load_data()
    search_results = []

    # Split the query into words
    query_words = query.split()

    def product_matches_query(product, query):
        # Helper function to check if the product matches the query
        main_category = product['main_category'].lower()
        sub_category = product['sub_category'].lower()
        product_name = product['product_name'].lower()

        if len(query_words) == 1:
            if query in main_category:
                return True
            sub_category_combined = sub_category.replace(' ', '')
            if query in sub_category_combined or query+'s' in sub_category_combined or query+'es' in sub_category_combined :
                return True
            elif query in product_name:
                return True
        elif len(query_words) == 2:
            if query in sub_category:
                return True
            elif (query_words[0].lower() in main_category and query_words[1].lower() in product_name) or (query_words[1].lower() in main_category and query_words[0].lower() in product_name):
                return True
            elif query in product_name:
                return True
        else:
            if query in main_category or query in sub_category or query in product_name:
                return True

        return False

    # Searching for matches in 'main_category', 'sub_category', and 'product_name' columns
    for product in all_data:
        if product_matches_query(product, query):
            search_results.append(product)
    random.shuffle(search_results)
    # Handle no rating display
    for product in search_results:
        if 'rating' not in product or product['rating'] is None:
            product['rating'] = 'None'

    # Pagination
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(search_results)
    pagination_search_results = search_results[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    return render_template('results.html',
                           search_results=pagination_search_results,
                           page=page,
                           per_page=per_page,
                           pagination=pagination,
                           query=query)

def get_similar_products(product_name, current_vendor):
    all_data = load_data()
    original_product_category = None
    similar_products = []

    # Find the category of the original product
    for product in all_data:
        if product['product_name'].lower() == product_name.lower():
            original_product_category = product['main_category'].lower()
            break

    # Collect similar products from different vendors in the same category
    for product in all_data:
        if product['vendor_name'] == current_vendor:
            first_word_match, remaining_similarity = is_similar(product_name.lower(), product['product_name'].lower())
            if first_word_match and (remaining_similarity > 0.3 or remaining_similarity == 0.0):
                if product['main_category'].lower() == original_product_category:
                    similar_products.append((product, remaining_similarity))

    # Sort similar products by remaining_similarity in descending order
    similar_products.sort(key=lambda x: x[1], reverse=True)

    # Extract only the product from the sorted list
    similar_products = [product for product, _ in similar_products]

    #random.shuffle(similar_products)
    return similar_products

@app.route('/similar/<vendor_name>/<product_name>')
def similar_products(vendor_name, product_name):
    similar_products = get_similar_products(product_name, vendor_name)
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(similar_products)
    pagination_similar_products = get_paginated_results(similar_products, page, per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    return render_template('similar_products.html',
                           similar_products=pagination_similar_products,
                           original_product=product_name,
                           page=page,
                           per_page=per_page,
                           pagination=pagination)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
