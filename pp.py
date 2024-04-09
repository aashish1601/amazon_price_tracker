from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import time
from email.message import EmailMessage
import ssl
import smtplib

app = Flask(__name__)

def send_email(receiver_email, product_title, product_price, threshold_price, amazon_url, sender_email, sender_password):
    subject = f"Price Drop Alert for {product_title}"
    body = f"The price of {product_title} has dropped to {product_price}. This is below your set threshold price of {threshold_price}. Visit the product page on Amazon: {amazon_url}"

    em = EmailMessage()
    em['From'] = sender_email
    em['To'] = receiver_email
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(em)

def scrape_amazon_product(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.amazon.in/'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        time.sleep(2)  
        soup = BeautifulSoup(response.text, 'html.parser')

        product_title_element = soup.find('span', {'id': 'productTitle'})
        product_price_whole_element = soup.find('span', {'class': 'a-price-whole'})
        product_price_decimal_element = soup.find('span', {'class': 'a-price-decimal'})

        product_title = product_title_element.get_text().strip() if product_title_element else None
        product_price_whole = product_price_whole_element.get_text().strip() if product_price_whole_element else None
        product_price_decimal = product_price_decimal_element.get_text().strip() if product_price_decimal_element else None

        product_price = f"{product_price_whole}.{product_price_decimal}" if product_price_whole and product_price_decimal else None

        product_description_element = soup.find('meta', {'name': 'description'})
        product_description = product_description_element['content'].strip() if product_description_element and 'content' in product_description_element.attrs else None

        return {"title": product_title, "price": product_price, "description": product_description}
    except requests.exceptions.RequestException as e:
        print(f"Error in scrape_amazon_product: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"Unexpected error in scrape_amazon_product: {e}")
        return {"error": "Unexpected error"}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        amazon_url = request.form['amazon_url']
        threshold_price = float(request.form['threshold_price'])
        receiver_email = request.form['receiver_email']
        sender_email = 'ashustuti2@gmail.com'  
        sender_password = 'wfyh dnbt jgur wfkg' 

        monitor_price(amazon_url, threshold_price, receiver_email, sender_email, sender_password)

    return render_template('python.html')

def monitor_price(url, threshold_price, receiver_email, sender_email, sender_password):
    while True:
        product_info = scrape_amazon_product(url)

        if 'error' in product_info:
            print(product_info)
        else:
            current_price = product_info['price']
            if current_price and isinstance(current_price, float) and current_price <= threshold_price:
                print(f"Sending email for {product_info['title']} with price {current_price}")
                send_email(receiver_email, product_info['title'], product_info['price'], threshold_price, url, sender_email, sender_password)
            else:
                send_email(receiver_email, product_info['title'], product_info['price'], threshold_price, url, sender_email, sender_password)
                
                

        time.sleep(3600) 

if __name__ == "__main__":
    app.run(debug=True)
