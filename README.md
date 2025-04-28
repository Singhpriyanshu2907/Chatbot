
# 🌿 Plantify Chat Assistant - Your AI-Powered Plant Shopping Companion
Transform your plant shopping experience with an intelligent chatbot that helps you discover, learn, and order plants effortlessly!

## 🚀 Why Plantify Chat Assistant?

#### ✅ Smart & Friendly - Get instant, accurate answers about plants, store info, and orders
#### ✅ Seamless Ordering - Add to cart, apply discounts, and checkout in natural conversation
#### ✅ 24/7 Support - No more waiting for business hours to get plant advice
#### ✅ Typos? No Problem! - Understands messy spelling ("snake plnt" → "Snake Plant")


## 🌟 Key Features

| Feature | Description | Tech Used |
|---------|-------------|-----------|
| **AI Guard** | Blocks off-topic questions while welcoming plant lovers | Mistral-7B LLM |
| **Intent Detection** | Knows when you want to order vs. ask questions | Context-aware classification |
| **Plant Encyclopedia** | Details on 40+ plants, herbs, and gardening supplies | Knowledge Base + Fuzzy Matching |
| **Cart Management** | "Add 2 peace lilies" → updates cart automatically | Regex + Product Catalog |
| **Discount Wizard** | Applies promo codes like "SPRING2023" with smart validation | Rule Engine |


## 🏗 How It Works

### 1. Multi-Agent Architecture

```mermaid
graph LR
    A[User Query] --> B{Guard Agent}
    B -->|Allowed| C[Classifier Agent]
    B -->|Blocked| D["🚫 Sorry, I can't help with that"]
    C -->|"Order?"| E[Order Agent]
    C -->|"Info?"| F[Details Agent]
    E --> G["🛒 Cart Updated!"]
    F --> H["🌱 Snake Plants love indirect sunlight!"]