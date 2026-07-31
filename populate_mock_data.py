import os
import django
import requests
from django.core.files.base import ContentFile
from decimal import Decimal
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pobon_maker_backend.settings')
django.setup()

from products.models import Category, Product, ProductImage

def populate_mock_data():
    print("Clearing existing products...")
    Product.objects.all().delete()
    
    # Make sure categories exist
    category_names = ['IPS', 'Induction', 'Inferet', 'Digital weightscale', 'Sound system', 'Gadget item']
    categories = {}
    for name in category_names:
        # Avoid slug collision
        from django.utils.text import slugify
        cat = Category.objects.filter(slug=slugify(name)).first()
        if not cat:
            cat = Category.objects.create(name=name)
        categories[name] = cat
        
    products_data = [
        # IPS
        {"name": "Luminous Eco Watt Neo 1050 Square Wave Inverter", "category": "IPS", "price": "6500.00", "stock": 15, "kw": "inverter,battery"},
        {"name": "Rahimafrooz 1000VA Pure Sine Wave IPS", "category": "IPS", "price": "12500.00", "stock": 5, "kw": "ips,power"},
        {"name": "Microtek UPS SEBz 1200 VA", "category": "IPS", "price": "8900.00", "stock": 20, "kw": "ups,power"},
        {"name": "Walton WIPS-1000 Inverter", "category": "IPS", "price": "9500.00", "stock": 0, "kw": "inverter"},
        
        # Induction
        {"name": "Miyako 2000W Induction Cooker", "category": "Induction", "price": "3200.00", "stock": 30, "kw": "induction,cooker"},
        {"name": "Vision Induction Cooker 1200W", "category": "Induction", "price": "2800.00", "stock": 2, "kw": "cooking,appliance"},
        {"name": "Walton WI-F15 Induction Cooker", "category": "Induction", "price": "3500.00", "stock": 45, "kw": "induction,kitchen"},
        
        # Inferet (Infrared Cooker)
        {"name": "Nova Infrared Cooker 2200W", "category": "Inferet", "price": "3800.00", "stock": 12, "kw": "infrared,cooker"},
        {"name": "Jaipan Infrared Cooker", "category": "Inferet", "price": "3100.00", "stock": 8, "kw": "stove,electric"},
        {"name": "Vision Infrared Cooker Elite", "category": "Inferet", "price": "4200.00", "stock": 1, "kw": "kitchen,appliance"},
        
        # Digital weightscale
        {"name": "Xiaomi Mi Body Composition Scale 2", "category": "Digital weightscale", "price": "2500.00", "stock": 50, "kw": "weight,scale"},
        {"name": "Camry Digital Glass Weighing Scale", "category": "Digital weightscale", "price": "1200.00", "stock": 18, "kw": "scale,glass"},
        {"name": "Beurer Digital Weight Scale GS 211", "category": "Digital weightscale", "price": "1800.00", "stock": 4, "kw": "digital,scale"},
        
        # Sound system
        {"name": "Logitech Z906 5.1 Surround Sound", "category": "Sound system", "price": "28500.00", "stock": 5, "kw": "speakers,audio"},
        {"name": "Edifier R1280T Powered Bookshelf Speakers", "category": "Sound system", "price": "8500.00", "stock": 10, "kw": "bookshelf,speakers"},
        {"name": "Fantech GS202 Sonic USB Bluetooth Speaker", "category": "Sound system", "price": "1500.00", "stock": 0, "kw": "bluetooth,speaker"},
        {"name": "Microlab M-106BT 2.1 Bluetooth Speaker", "category": "Sound system", "price": "3200.00", "stock": 25, "kw": "subwoofer,sound"},
        
        # Gadget item
        {"name": "Apple AirPods Pro (2nd Gen)", "category": "Gadget item", "price": "25000.00", "stock": 10, "kw": "earbuds,apple"},
        {"name": "Samsung Galaxy SmartTag2", "category": "Gadget item", "price": "3500.00", "stock": 100, "kw": "smart,tracker"},
        {"name": "Anker PowerCore 10000mAh Power Bank", "category": "Gadget item", "price": "2200.00", "stock": 40, "kw": "powerbank,charger"},
        {"name": "Baseus 65W GaN Fast Charger", "category": "Gadget item", "price": "2800.00", "stock": 7, "kw": "charger,adapter"},
    ]

    # Generate 100 more random products
    for i in range(1, 101):
        cat_name = random.choice(category_names)
        products_data.append({
            "name": f"Mock Product {i} - {cat_name}",
            "category": cat_name,
            "price": str(random.randint(500, 25000)) + ".00",
            "stock": random.randint(0, 50),
            "kw": "electronics,product"
        })

    print(f"Creating {len(products_data)} products...")
    
    for idx, p_data in enumerate(products_data):
        print(f"[{idx+1}/{len(products_data)}] Creating: {p_data['name']}")
        
        product = Product.objects.create(
            name=p_data['name'],
            category=categories[p_data['category']],
            price=Decimal(p_data['price']),
            stock_count=p_data['stock'],
            description=f"High quality {p_data['name']} designed for long lasting durability and excellent performance. Best in the {p_data['category']} category."
        )
        
        # Download a random image from loremflickr using the keyword
        image_url = f"https://loremflickr.com/800/600/{p_data['kw']}"
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                image_name = f"{product.sku}_cover.jpg"
                
                # Save as cover image
                pi = ProductImage(product=product, is_cover=True)
                pi.image.save(image_name, ContentFile(response.content), save=True)
                
                # Try downloading a second image for variety (non-cover)
                response2 = requests.get(image_url, timeout=10)
                if response2.status_code == 200:
                    image_name2 = f"{product.sku}_2.jpg"
                    pi2 = ProductImage(product=product, is_cover=False)
                    pi2.image.save(image_name2, ContentFile(response2.content), save=True)
                    
        except Exception as e:
            print(f"  - Failed to download image for {product.name}: {e}")

    print("Mock data population complete!")

if __name__ == '__main__':
    populate_mock_data()
