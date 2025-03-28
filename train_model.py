# train_model.py
import json
import pickle
import numpy as np
import os
import random
from datetime import datetime
from sklearn.linear_model import LinearRegression

class BillingModel:
    def __init__(self, model_path='models/billing_model.pkl', data_path='data/customer_data.json'):
        self.model_path = model_path
        self.data_path = data_path
        self.model = None
        self.customer_data = {}
        self.load_customer_data()
    
    def load_customer_data(self):
        """Load customer data from JSON file"""
        try:
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            
            # Check if file exists, create if not
            if not os.path.exists(self.data_path):
                print(f"Customer data file not found. Creating empty data file.")
                self.customer_data = {
                    "C100001": {
                        "customer_id": "C100001",
                        "first_seen": datetime.now().strftime("%Y-%m-%d"),
                        "visit_count": 1,
                        "purchases": [
                            {
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "amount": 85.50,
                                "items_count": 5
                            }
                        ],
                        "avg_bill": 85.50
                    },
                    "C100002": {
                        "customer_id": "C100002",
                        "first_seen": datetime.now().strftime("%Y-%m-%d"),
                        "visit_count": 2,
                        "purchases": [
                            {
                                "date": (datetime.now().replace(day=datetime.now().day-5)).strftime("%Y-%m-%d"),
                                "amount": 65.25,
                                "items_count": 3
                            },
                            {
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "amount": 120.75,
                                "items_count": 8
                            }
                        ],
                        "avg_bill": 93.00
                    }
                }
                self.save_customer_data()
                return True
                
            with open(self.data_path, 'r') as f:
                self.customer_data = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading customer data: {e}")
            self.customer_data = {}
            return False
    
    def save_customer_data(self):
        """Save customer data to JSON file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            
            with open(self.data_path, 'w') as f:
                json.dump(self.customer_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving customer data: {e}")
            return False
    
    def load_model(self):
        """Load trained model from pickle file"""
        try:
            if not os.path.exists(self.model_path):
                print("Model file not found.")
                return False
                
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def save_model(self):
        """Save model to pickle file"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def prepare_training_data(self):
        """Prepare training data from customer purchase history"""
        X = []  # Features (previous bill)
        y = []  # Target (current bill)
        
        for customer_id, data in self.customer_data.items():
            purchases = data.get('purchases', [])
            
            # Need at least 2 purchases to create a training pair
            if len(purchases) < 2:
                continue
            
            # Create training pairs from sequential purchases
            for i in range(1, len(purchases)):
                prev_amount = purchases[i-1]['amount']
                current_amount = purchases[i]['amount']
                
                X.append([prev_amount])
                y.append(current_amount)
        
        if not X:
            return None, None
            
        return np.array(X), np.array(y)
    
    def train(self):
        """Train the billing prediction model"""
        X, y = self.prepare_training_data()
        
        if X is None or len(X) < 2:
            print("Not enough data for training. Creating simple model.")
            # Create a simple model that adds random variation to the average bill
            self.model = {
                'type': 'simple',
                'avg_bill': 100.0  # Default average bill
            }
            
            # Calculate actual average if we have data
            bill_amounts = []
            for customer_data in self.customer_data.values():
                for purchase in customer_data.get('purchases', []):
                    bill_amounts.append(purchase['amount'])
            
            if bill_amounts:
                self.model['avg_bill'] = sum(bill_amounts) / len(bill_amounts)
        else:
            print(f"Training linear regression model with {len(X)} samples.")
            # Create and train linear regression model
            self.model = {
                'type': 'linear_regression',
                'model': LinearRegression().fit(X, y)
            }
        
        return self.save_model()
    
    def predict(self, customer_id):
        """Predict bill amount for customer"""
        if not self.model:
            self.load_model()
            if not self.model:
                return 100.0  # Default prediction if model loading fails
        
        customer = self.customer_data.get(customer_id)
        
        # If customer not found, return default prediction
        if not customer:
            if isinstance(self.model, dict) and self.model.get('type') == 'simple':
                return self.model['avg_bill'] * (1 + random.uniform(-0.1, 0.1))
            else:
                # Use average of all training data
                return 100.0  # Default prediction
        
        # Get purchase history
        purchases = customer.get('purchases', [])
        
        # If no purchase history, return default prediction
        if not purchases:
            if isinstance(self.model, dict) and self.model.get('type') == 'simple':
                return self.model['avg_bill'] * (1 + random.uniform(-0.1, 0.1))
            else:
                # Use average of all training data
                return 100.0  # Default prediction
        
        # Get most recent purchase amount
        last_purchase_amount = purchases[-1]['amount']
        
        # Make prediction
        if isinstance(self.model, dict) and self.model.get('type') == 'simple':
            # For simple model, use weighted average of last purchase and overall average
            prediction = 0.7 * last_purchase_amount + 0.3 * self.model['avg_bill']
            # Add small random variation
            prediction *= (1 + random.uniform(-0.05, 0.05))
        else:
            # For linear regression model or unknown model type
            if isinstance(self.model, dict) and 'model' in self.model:
                prediction = self.model['model'].predict([[last_purchase_amount]])[0]
            else:
                # Fallback if model structure is unexpected
                prediction = last_purchase_amount * (1 + random.uniform(-0.1, 0.1))
        
        return prediction
    
    def update_with_new_purchase(self, customer_id, amount):
        """Update customer data with new purchase and retrain model"""
        # Load latest data
        self.load_customer_data()
        
        # Check if customer exists
        if customer_id not in self.customer_data:
            # Create new customer
            self.customer_data[customer_id] = {
                'customer_id': customer_id,
                'first_seen': datetime.now().strftime("%Y-%m-%d"),
                'visit_count': 1,
                'purchases': []
            }
        
        # Add new purchase
        new_purchase = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'amount': amount,
            'items_count': random.randint(1, 20)  # Random item count for demonstration
        }
        
        if 'purchases' not in self.customer_data[customer_id]:
            self.customer_data[customer_id]['purchases'] = []
            
        self.customer_data[customer_id]['purchases'].append(new_purchase)
        
        # Update visit count
        self.customer_data[customer_id]['visit_count'] = len(self.customer_data[customer_id]['purchases'])
        
        # Calculate average bill
        amounts = [p['amount'] for p in self.customer_data[customer_id]['purchases']]
        self.customer_data[customer_id]['avg_bill'] = sum(amounts) / len(amounts)
        
        # Save updated data
        self.save_customer_data()
        
        # Retrain model with new data
        self.train()
        
        return True

# Test function to run if script is executed directly
if __name__ == "__main__":
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    # Initialize and train model
    model = BillingModel()
    model.train()
    
    # Test prediction
    for customer_id in model.customer_data:
        prediction = model.predict(customer_id)
        print(f"Customer {customer_id} prediction: ${prediction:.2f}")