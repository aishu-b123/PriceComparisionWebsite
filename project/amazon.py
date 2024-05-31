import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
}

def get_product_data(url, category, max_products=200):
    products = []
    page = 1

    while len(products) < max_products:
        print(f"Fetching page {page} for {category}")
        response = requests.get(f"{url}&page={page}", headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        items = soup.select('div[data-component-type="s-search-result"]')
        print(f"Found {len(items)} items on page {page} for {category}")

        if not items:
            break

        for item in items:
            if len(products) >= max_products:
                break

            try:
                name = item.h2.text.strip() if item.h2 else None
                image_tag = item.find('img', {'class': 's-image'})
                image = image_tag['src'] if image_tag else None
                
                # Extract price
                price_whole = item.find('span', {'class': 'a-price-whole'})
                price_fraction = item.find('span', {'class': 'a-price-fraction'})
                price = None
                if price_whole and price_fraction:
                    price = f"{price_whole.text}.{price_fraction.text}"
                elif price_whole:
                    price = price_whole.text
                elif price_fraction:
                    price = price_fraction.text
                
                rating_tag = item.find('span', {'class': 'a-icon-alt'})
                rating = rating_tag.text.split(' ')[0] if rating_tag else None
                
                link_tag = item.find('a', {'class': 'a-link-normal s-no-outline'})
                link = 'https://www.amazon.in' + link_tag['href'] if link_tag else None
                
                discount_tag = item.find('span', {'class': 'a-price a-text-price'})
                discount = discount_tag.text.strip() if discount_tag else None

                if name and image and price and link:
                    products.append({
                        'Product Name': name,
                        'Image URL': image,
                        'Price': price,
                        'Rating': rating,
                        'Discount': discount,
                        'Link': link,
                        'Category': category
                    })
            except Exception as e:
                print(f"Error processing item: {e}")

        page += 1
        time.sleep(2)  # Respectful delay to avoid being blocked

    return products

def scrape_and_save(categories, max_products=200):
    all_products = []

    for category, search_url in categories.items():
        products = get_product_data(search_url, category, max_products)
        all_products.extend(products)

    df = pd.DataFrame(all_products)
    df.to_csv('amazon_products9.csv', index=False)
    print("Data has been written to amazon_products.csv")

categories = {
    #'Phones': "https://www.amazon.in/s?k=phones",
    #'Laptops': "https://www.amazon.in/s?k=laptops",
    'Watches': "https://www.amazon.in/s?k=watches",
    #'Cameras': "https://www.amazon.in/s?k=camera",
    #'Bluetooth Speakers': "https://www.amazon.in/s?k=bluetooth+speakers",
    #'Smart Gadgets': "https://www.amazon.in/s?k=smart+gadgets"
}

scrape_and_save(categories, max_products=200)
