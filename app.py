from flask import Flask, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

app = Flask(__name__)
CORS(app)

# Global ML Model
model = None
training_stats = {}

def generate_irrigation_data(n=8000):
    np.random.seed(42)
    data = {
        'soil_moisture': np.random.uniform(5, 85, n),
        'temperature': np.random.uniform(15, 45, n),
        'humidity': np.random.uniform(20, 100, n),
        'rainfall_historical': np.random.uniform(0, 300, n)
    }
    df = pd.DataFrame(data)
    df['irrigation_needed'] = (
        (df['soil_moisture'] < 35) & 
        (df['temperature'] > 30) & 
        (df['humidity'] < 60) & 
        (df['rainfall_historical'] < 50)
    ).astype(int)
    df['water_quantity'] = np.where(df['irrigation_needed'] == 1,
        25 * (35 - df['soil_moisture']) * (df['temperature'] / 30),
        0)
    return df

def train_model():
    global model, training_stats
    df = generate_irrigation_data()
    X = df[['soil_moisture', 'temperature', 'humidity', 'rainfall_historical']]
    y = df['irrigation_needed']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    training_stats = {
        'accuracy': accuracy_score(y_test, y_pred),
        'importance': dict(zip(X.columns, model.feature_importances_))
    }
    print("✅ MODEL TRAINED - OUTPUT READY!")

@app.route('/')
def home():
    if model is None:
        train_model()
    
    # HTML EMBEDDED - NO SEPARATE FILES NEEDED
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌊 Irrigation ML Predictor</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background: linear-gradient(135deg, #74b9ff, #0984e3); min-height: 100vh; padding: 20px; }}
            .card {{ border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }}
            .result-yes {{ background: linear-gradient(45deg, #ff6b6b, #ee5a52); color: white; }}
            .result-no {{ background: linear-gradient(45deg, #00b894, #00cec9); color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="text-center mb-5 text-white">🌾 Smart Irrigation System [ML]</h1>
            
            <div class="row">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-warning text-dark">
                            <h4>📊 Enter Sensor Data</h4>
                        </div>
                        <div class="card-body">
                            <form id="predictForm">
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <label>Soil Moisture (%)</label>
                                        <input type="number" class="form-control" id="soil" min="5" max="85" value="28">
                                    </div>
                                    <div class="col-md-6">
                                        <label>Temperature (°C)</label>
                                        <input type="number" class="form-control" id="temp" min="15" max="45" value="34">
                                    </div>
                                    <div class="col-md-6">
                                        <label>Humidity (%)</label>
                                        <input type="number" class="form-control" id="hum" min="20" max="100" value="55">
                                    </div>
                                    <div class="col-md-6">
                                        <label>Rainfall (7d mm)</label>
                                        <input type="number" class="form-control" id="rain" min="0" max="300" value="25">
                                    </div>
                                </div>
                                <button type="submit" class="btn btn-success w-100 mt-4 btn-lg">🚿 PREDICT</button>
                            </form>
                            <div id="result" class="mt-4"></div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h5>🤖 ML Stats</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>Accuracy:</strong> {training_stats['accuracy']:.1%}</p>
                            <p><strong>Soil Moisture:</strong> {training_stats['importance']['soil_moisture']:.1%}</p>
                            <p><strong>Temperature:</strong> {training_stats['importance']['temperature']:.1%}</p>
                            <p><strong>Humidity:</strong> {training_stats['importance']['humidity']:.1%}</p>
                            <p><strong>Rainfall:</strong> {training_stats['importance']['rainfall_historical']:.1%}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        document.getElementById('predictForm').onsubmit = async function(e) {{
            e.preventDefault();
            const soil = parseFloat(document.getElementById('soil').value);
            const temp = parseFloat(document.getElementById('temp').value);
            const hum = parseFloat(document.getElementById('hum').value);
            const rain = parseFloat(document.getElementById('rain').value);
            
            const response = await fetch('/predict', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    soil_moisture: soil,
                    temperature: temp,
                    humidity: hum,
                    rainfall_historical: rain
                }})
            }});
            const result = await response.json();
            
            document.getElementById('result').innerHTML = `
                <div class="alert ${{result.needs_water ? 'result-yes' : 'result-no'}} p-4">
                    <h3><strong>${{result.needs_water ? '🚿 YES' : '✅ NO'}}</strong> Irrigation!</h3>
                    <h4>💧 ${{result.water_qty}} Liters</h4>
                    <p>Confidence: ${{ (result.probability * 100).toFixed(1) }}%</p>
                    <hr>
                    <small>Soil: ${{soil}}% | Temp: ${{temp}}°C | Hum: ${{hum}}% | Rain: ${{rain}}mm</small>
                </div>`;
        }};
        </script>
    </body>
    </html>
    """
    return html

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        train_model()
    
    data = request.get_json()
    print("Received data:", data)
    soil = float(data['soil_moisture'])
    temp = float(data['temperature'])
    hum = float(data['humidity'])
    rain = float(data['rainfall_historical'])
    
    input_data = [[soil, temp, hum, rain]]
    print("Input data:", input_data)
    prediction = model.predict(input_data)[0]
    probability = model.predict_proba(input_data)[0][1]  # prob of 1
    
    needs_water = prediction == 1
    water_qty = 0
    if needs_water:
        water_qty = round(25 * (35 - soil) * (temp / 30), 1)
    
    return {
        'needs_water': bool(needs_water),
        'water_qty': float(water_qty),
        'probability': float(round(probability, 2))
    }

if __name__ == '__main__':
    app.run(port=8000, host='127.0.0.1')