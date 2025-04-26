import os
import json
from copy import deepcopy
import re
import boto3
from dotenv import load_dotenv
from datetime import datetime
from .utils import get_chatbot_response

load_dotenv()

class OrderTakingAgent():
    def __init__(self):
        # Initialize Bedrock client
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.model_name = os.getenv("BEDROCK_MODEL_NAME", "mistral.mistral-7b-instruct-v0:2")
        
        # Product catalog with prices
        self.products = [
            {"name": "White Butterfly (Syngonium Podophyllum)", "price": 100},
            {"name": "Peace Lily", "price": 150},
            {"name": "Chlorophytum Spider Plant", "price": 100},
            {"name": "Money Plant Marble Prince", "price": 150},
            {"name": "Snake Plant (Sansevieria)", "price": 200},
            {"name": "Aglaonema Lipstick", "price": 300},
            {"name": "Jade Plant (Portulacaria afra)", "price": 200},
            {"name": "Rubber Tree (Ficus elastica)", "price": 300},
            {"name": "Krishna Tulsi Plant (Black)", "price": 50},
            {"name": "Lemon Grass", "price": 50},
            {"name": "Curry Leaves", "price": 50},
            {"name": "Rama Tulsi Plant", "price": 50},
            {"name": "Ajwain Leaves", "price": 100},
            {"name": "Mentha Arvensis (Japanese Mint)", "price": 100},
            {"name": "Black Turmeric Plant (Black Haldi)", "price": 300},
            {"name": "Bhuiamla", "price": 100},
            {"name": "Wild Asparagus", "price": 200},
            {"name": "Jasminum sambac", "price": 150},
            {"name": "Parijat Tree", "price": 300},
            {"name": "Rose", "price": 100},
            {"name": "Raat Rani", "price": 200},
            {"name": "Shevanti", "price": 100},
            {"name": "Marigold (Orange)", "price": 50},
            {"name": "Champa (White)", "price": 200},
            {"name": "Rajnigandha", "price": 100},
            {"name": "Fragrant Panama rose", "price": 300},
            {"name": "Pincushion Cactus", "price": 150},
            {"name": "Bunny Ear Cactus", "price": 200},
            {"name": "Echinopsis chamaecereus", "price": 250},
            {"name": "Golden Pipe Cactus", "price": 300},
            {"name": "Moon Cactus (Grafted)", "price": 300},
            {"name": "Graptoveria opalina", "price": 250},
            {"name": "Crassula tetragona", "price": 200},
            {"name": "Aloe Vera", "price": 100},
            {"name": "Euphorbia (Red)", "price": 300},
            {"name": "Vermicompost", "price": 10, "unit": "kg"},
            {"name": "Vermicompost Mixture", "price": 20, "unit": "kg"},
            {"name": "Dec-Neemo (Bio-fertilizer)", "price": 150, "unit": "ltr"},
            {"name": "Dec-Mori (Bio-fertilizer)", "price": 150, "unit": "ltr"},
            {"name": "Agni Shield", "price": 300}
        ]
        
        # Product categories mapping
        self.product_categories = {
            "Plants": ["White Butterfly (Syngonium Podophyllum)", "Peace Lily", "Chlorophytum Spider Plant", 
                      "Money Plant Marble Prince", "Snake Plant (Sansevieria)", "Aglaonema Lipstick", 
                      "Jade Plant (Portulacaria afra)", "Rubber Tree (Ficus elastica)"],
            "Herbs": ["Krishna Tulsi Plant (Black)", "Lemon Grass", "Curry Leaves", "Rama Tulsi Plant", 
                     "Ajwain Leaves", "Mentha Arvensis (Japanese Mint)", "Black Turmeric Plant (Black Haldi)", 
                     "Bhuiamla", "Wild Asparagus"],
            "Flowers": ["Jasminum sambac", "Parijat Tree", "Rose", "Raat Rani", "Shevanti", "Marigold (Orange)", 
                       "Champa (White)", "Rajnigandha", "Fragrant Panama rose"],
            "Cacti": ["Pincushion Cactus", "Bunny Ear Cactus", "Echinopsis chamaecereus", 
                     "Golden Pipe Cactus", "Moon Cactus (Grafted)"],
            "Succulents": ["Graptoveria opalina", "Crassula tetragona", "Aloe Vera", "Euphorbia (Red)"],
            "Plant Care": ["Vermicompost", "Vermicompost Mixture", "Dec-Neemo (Bio-fertilizer)", 
                          "Dec-Mori (Bio-fertilizer)", "Agni Shield"]
        }
        
        # Special offers and discounts
        self.discounts = {
            "WELCOME10": {"type": "percent", "value": 10, "min_purchase": 50},
            "SPRING2023": {"type": "percent", "value": 15, "min_purchase": 75},
            "FREESHIP": {"type": "shipping", "value": 9.99, "min_purchase": 100},
        }
        
        # Shipping rates
        self.shipping_rates = {
            "standard": 9.99,
            "express": 19.99
        }
        
        # Tax rate (in percent)
        self.tax_rate = 8.5
    
    def _extract_items(self, user_message):
        """
        Extract product items and quantities from user message
        Returns a list of tuples (item, quantity)
        """
        # Normalize message
        message = user_message.lower().strip()
        
        # Look for explicit quantities
        quantity_patterns = [
            r'(\d+)\s+([a-z\s]+?)(?:,|\s+and\s+|$)',  # "2 peace lily"
            r'([a-z\s]+?)\s+x\s*(\d+)(?:,|\s+and\s+|$)',  # "peace lily x2"
            r'([a-z\s]+?)(?:\s+|-\s*)(\d+)(?:,|\s+and\s+|$)',  # "peace lily - 2"
        ]
        
        found_items = []
        for pattern in quantity_patterns:
            for match in re.finditer(pattern, message):
                if match.group(1).isdigit():  # First pattern
                    quantity = int(match.group(1))
                    item = match.group(2).strip()
                else:  # Other patterns
                    item = match.group(1).strip()
                    quantity = int(match.group(2))
                found_items.append((item, quantity))
                
        # If no items with quantities found, look for product names and assume quantity 1
        if not found_items:
            # Get all product names as a flat list
            all_products = [product["name"].lower() for product in self.products]
            
            # Look for product mentions
            for product_name in all_products:
                if product_name.lower() in message:
                    found_items.append((product_name, 1))
            
            # If still no exact matches, check for partial matches
            if not found_items:
                for product_name in all_products:
                    product_words = product_name.lower().split()
                    # Check if any key words from product names are in the message
                    if any(word in message for word in product_words if len(word) > 3):
                        found_items.append((product_name, 1))
        
        return found_items
    
    def _find_product_in_catalog(self, product_name):
        """
        Find a product in the catalog with fuzzy matching
        Returns (category, product_name, price) or None if not found
        """
        product_name = product_name.lower().strip()
        
        # Exact match
        for product in self.products:
            if product["name"].lower() == product_name:
                # Find category
                category = "Other"
                for cat, products in self.product_categories.items():
                    if product["name"] in products:
                        category = cat
                        break
                return category, product["name"], product["price"]
        
        # Partial match (if product name is in catalog entry)
        for product in self.products:
            catalog_product = product["name"].lower()
            if product_name in catalog_product or catalog_product in product_name:
                # Find category
                category = "Other"
                for cat, products in self.product_categories.items():
                    if product["name"] in products:
                        category = cat
                        break
                return category, product["name"], product["price"]
        
        return None
    
    def _calculate_total(self, cart, applied_discounts=None):
        """
        Calculate the total bill with applied discounts
        """
        subtotal = sum(item["price"] * item["quantity"] for item in cart)
        shipping = self.shipping_rates["standard"]
        discount_amount = 0
        
        # Apply discounts
        if applied_discounts:
            for code in applied_discounts:
                if code in self.discounts:
                    discount = self.discounts[code]
                    if subtotal >= discount["min_purchase"]:
                        if discount["type"] == "percent":
                            discount_amount += subtotal * (discount["value"] / 100)
                        elif discount["type"] == "shipping":
                            shipping = 0
        
        # Calculate tax
        tax = (subtotal - discount_amount) * (self.tax_rate / 100)
        
        # Calculate grand total
        total = subtotal - discount_amount + shipping + tax
        
        return {
            "subtotal": round(subtotal, 2),
            "discount": round(discount_amount, 2),
            "shipping": round(shipping, 2),
            "tax": round(tax, 2),
            "total": round(total, 2)
        }
    
    def _parse_memory(self, messages):
        """
        Extract memory from previous messages
        """
        cart = []
        discount_codes = []
        
        for message in messages:
            if message.get("role") == "assistant" and "memory" in message:
                memory = message.get("memory", {})
                if memory.get("agent") == "order_taking_agent":
                    if "cart" in memory:
                        cart = memory["cart"]
                    if "discount_codes" in memory:
                        discount_codes = memory["discount_codes"]
        
        return cart, discount_codes
    
    def _format_cart_summary(self, cart, totals):
        """
        Format cart summary for display
        """
        summary = "Your current cart:\n"
        
        # Group by category
        by_category = {}
        for item in cart:
            category = item["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(item)
        
        # Format items by category
        for category, items in by_category.items():
            summary += f"\n{category.upper()}:\n"
            for item in items:
                item_total = item["price"] * item["quantity"]
                summary += f"- {item['name']} (${item['price']:.2f}) x {item['quantity']} = ${item_total:.2f}\n"
        
        # Format totals
        summary += f"\nSubtotal: ${totals['subtotal']:.2f}"
        if totals['discount'] > 0:
            summary += f"\nDiscount: -${totals['discount']:.2f}"
        summary += f"\nShipping: ${totals['shipping']:.2f}"
        summary += f"\nTax ({self.tax_rate}%): ${totals['tax']:.2f}"
        summary += f"\nTotal: ${totals['total']:.2f}"
        
        return summary
    
    def get_response(self, messages):
        """
        Process user message and generate response for order taking
        """
        try:
            # Extract latest user message
            user_message = messages[-1]['content']
            
            # Get existing cart and discount codes from memory
            cart, discount_codes = self._parse_memory(messages)
            
            # Handle checkout intent
            if re.search(r'\b(checkout|place\s+order|pay|finish|complete\s+order)\b', user_message.lower()):
                # Calculate totals
                totals = self._calculate_total(cart, discount_codes)
                
                # Generate checkout response
                summary = self._format_cart_summary(cart, totals)
                response = f"Thank you for your order! Here's your order summary:\n\n{summary}\n\nYour order has been confirmed. You'll receive a confirmation email shortly."
                
                # Reset cart after checkout
                cart = []
                discount_codes = []
                
                return {
                    "role": "assistant",
                    "content": response,
                    "memory": {
                        "agent": "order_taking_agent",
                        "action": "checkout_complete",
                        "cart": cart,
                        "discount_codes": discount_codes,
                        "totals": totals
                    }
                }
            
            # Handle discount code
            discount_match = re.search(r'\b(code|discount|promo|coupon)[\s:]*([\w\d]+)\b', user_message, re.IGNORECASE)
            if discount_match:
                code = discount_match.group(2).upper()
                if code in self.discounts:
                    if code not in discount_codes:
                        discount_codes.append(code)
                        discount_info = self.discounts[code]
                        discount_type = f"{discount_info['value']}% off" if discount_info['type'] == 'percent' else "free shipping"
                        response = f"Great! I've applied discount code {code} for {discount_type} on orders over ${discount_info['min_purchase']:.2f}."
                    else:
                        response = f"The discount code {code} is already applied to your order."
                else:
                    response = f"Sorry, the discount code {code} is not valid. Please try another code."
                
                # Calculate updated totals
                totals = self._calculate_total(cart, discount_codes)
                
                # Add cart summary if there are items
                if cart:
                    response += "\n\n" + self._format_cart_summary(cart, totals)
                
                return {
                    "role": "assistant",
                    "content": response,
                    "memory": {
                        "agent": "order_taking_agent",
                        "action": "apply_discount",
                        "cart": cart,
                        "discount_codes": discount_codes,
                        "totals": totals
                    }
                }
            
            # Handle cart inquiry
            if re.search(r'\b(cart|basket|order|what.*added|what.*ordered|show.*items)\b', user_message.lower()):
                if not cart:
                    return {
                        "role": "assistant",
                        "content": "Your cart is currently empty. Would you like to add some plants or supplies?",
                        "memory": {
                            "agent": "order_taking_agent",
                            "action": "show_cart",
                            "cart": cart,
                            "discount_codes": discount_codes
                        }
                    }
                
                # Calculate totals
                totals = self._calculate_total(cart, discount_codes)
                
                # Generate cart summary
                summary = self._format_cart_summary(cart, totals)
                response = f"{summary}\n\nWould you like to add more items or proceed to checkout?"
                
                return {
                    "role": "assistant",
                    "content": response,
                    "memory": {
                        "agent": "order_taking_agent",
                        "action": "show_cart",
                        "cart": cart,
                        "discount_codes": discount_codes,
                        "totals": totals
                    }
                }
            
            # Extract items from message
            extracted_items = self._extract_items(user_message)
            
            # If items found, add to cart
            if extracted_items:
                added_items = []
                not_found_items = []
                
                for item_name, quantity in extracted_items:
                    product_info = self._find_product_in_catalog(item_name)
                    
                    if product_info:
                        category, product_name, price = product_info
                        
                        # Check if item already in cart
                        existing_item = next((i for i in cart if i["name"] == product_name), None)
                        
                        if existing_item:
                            existing_item["quantity"] += quantity
                            added_items.append((product_name, quantity, existing_item["quantity"]))
                        else:
                            cart.append({
                                "category": category,
                                "name": product_name,
                                "price": price,
                                "quantity": quantity
                            })
                            added_items.append((product_name, quantity, quantity))
                    else:
                        not_found_items.append(item_name)
                
                # Generate response
                if added_items:
                    response_parts = []
                    for name, qty, total_qty in added_items:
                        if qty == total_qty:
                            response_parts.append(f"{qty} {name}")
                        else:
                            response_parts.append(f"{qty} more {name} (total: {total_qty})")
                    
                    response = f"I've added {', '.join(response_parts)} to your cart."
                    
                    if not_found_items:
                        response += f"\n\nI couldn't find these items: {', '.join(not_found_items)}. Would you like me to suggest alternatives?"
                    
                    # Calculate totals
                    totals = self._calculate_total(cart, discount_codes)
                    
                    # Add cart summary
                    response += "\n\n" + self._format_cart_summary(cart, totals)
                    
                    return {
                        "role": "assistant",
                        "content": response,
                        "memory": {
                            "agent": "order_taking_agent",
                            "action": "add_to_cart",
                            "cart": cart,
                            "discount_codes": discount_codes,
                            "totals": totals
                        }
                    }
                elif not_found_items:
                    response = f"I couldn't find these items: {', '.join(not_found_items)}. Could you please specify which plants or supplies you're looking for?"
                    
                    return {
                        "role": "assistant",
                        "content": response,
                        "memory": {
                            "agent": "order_taking_agent",
                            "action": "items_not_found",
                            "cart": cart,
                            "discount_codes": discount_codes,
                            "not_found": not_found_items
                        }
                    }
            
            # If we reach here, use LLM to handle the request
            system_prompt = """<<SYS>> You are a helpful assistant for an Indian plant shop. Your task is to help customers with their plant orders.

Available product categories:
1. Plants: White Butterfly (Syngonium), Peace Lily, Spider Plant, Money Plant, Snake Plant, Aglaonema Lipstick, Jade Plant, Rubber Tree
2. Herbs: Krishna Tulsi, Lemon Grass, Curry Leaves, Rama Tulsi, Ajwain Leaves, Japanese Mint, Black Turmeric, Bhuiamla, Wild Asparagus
3. Flowers: Jasminum sambac, Parijat Tree, Rose, Raat Rani, Shevanti, Marigold, Champa, Rajnigandha, Panama Rose
4. Cacti: Pincushion Cactus, Bunny Ear Cactus, Echinopsis chamaecereus, Golden Pipe Cactus, Moon Cactus
5. Succulents: Graptoveria opalina, Crassula tetragona, Aloevera, Euphorbia (Red)
6. Plant Care: Vermicompost, Vermicompost Mixture, Dec-Neemo, Dec-Mori, Agni Shield

When helping customers:
1. Be helpful and informative about plant care.
2. Encourage customers to add items to their cart.
3. Offer relevant product suggestions based on their interests.
4. If they want to order, help them be specific about what they want.
5. Mention prices in Indian Rupees (₹) as listed in the product data.
6. Remind customers of any current discounts:
   - WELCOME10: 10% off orders over ₹500
   - SPRING2023: 15% off orders over ₹750
   - FREESHIP: Free shipping on orders over ₹1000

Reply in a friendly, helpful manner fitting for an Indian plant shop assistant.
<</SYS>>"""

            # Prepare context for the model
            context = f"The customer currently has {len(cart)} items in their cart."
            if cart:
                totals = self._calculate_total(cart, discount_codes)
                context += f" Cart total: ${totals['total']:.2f}."
            if discount_codes:
                context += f" Applied discount codes: {', '.join(discount_codes)}."
            
            # Format messages for the model
            messages_for_model = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {context}\n\nCustomer: {user_message}"}
            ]
            
            # Get response from the model
            response = get_chatbot_response(
                client=self.client,
                model_name=self.model_name,
                messages=messages_for_model,
                temperature=0.7,
                max_tokens=500
            )
            
            return {
                "role": "assistant",
                "content": response.strip(),
                "memory": {
                    "agent": "order_taking_agent",
                    "action": "general_response",
                    "cart": cart,
                    "discount_codes": discount_codes
                }
            }
            
        except Exception as e:
            print(f"OrderTakingAgent error: {str(e)}")
            return {
                "role": "assistant",
                "content": "I'm sorry, there was an error processing your order. Please try again.",
                "memory": {
                    "agent": "order_taking_agent",
                    "error": str(e)
                }
            }