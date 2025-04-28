
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

## 📈 What Makes This Special?

| Feature | Description |
|---------|-------------|
| 🌱 **Retail-Tuned AI** | Not just a chatbot - built specifically for plant stores |
| 🛡️ **Fail-Safe Design** | Defaults to helpful mode when uncertain |
| 🛠️ **Extensible** | Add new plants by editing `order_taking_agent.py` |


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


## Tech Stack

**Core AI:** AWS Bedrock + Mistral-7B

**Conversation Flow:** Node, Express

**Error Handling** Auto-recovery from typos/ambiguities

**Frontend** Streamlit with botanical UI


## 🛠 Setup

Install dependencies (Python 3.10+ required)

```bash
  pip install -r requirements.txt
```
Configure AWS credentials

```bash
  pip install -r requirements.txt
```
Launch!

```bash
  streamlit run python_code/main.py
```
## 🌈 See It in Action

**Scenario**: Customer wants snake plants but misspells it 

```python
User: "How much for 3 snak plantas?"  
Bot: "🪴 Found 'Snake Plant'! 3 x ₹200 = ₹600. Add to cart?"  

User: "Apply code SPRING2023"  
Bot: "🌸 15% discount applied! New total: ₹510"  



## License

[MIT](https://choosealicense.com/licenses/mit/)

