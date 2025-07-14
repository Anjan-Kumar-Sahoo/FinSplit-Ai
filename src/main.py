"""
FinSplit - Expense Sharing Application
A Django-based web application for splitting expenses among groups.
"""
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    """Home page with information about FinSplit."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FinSplit - Split Expenses Easily</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                text-align: center;
                padding: 60px 0;
            }
            .header h1 {
                font-size: 3.5rem;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .header p {
                font-size: 1.3rem;
                opacity: 0.9;
                max-width: 600px;
                margin: 0 auto;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                margin: 60px 0;
            }
            .feature {
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }
            .feature h3 {
                font-size: 1.5rem;
                margin-bottom: 15px;
                color: #ffd700;
            }
            .feature p {
                opacity: 0.9;
                line-height: 1.6;
            }
            .cta {
                text-align: center;
                margin: 60px 0;
            }
            .btn {
                display: inline-block;
                padding: 15px 30px;
                background: #ffd700;
                color: #333;
                text-decoration: none;
                border-radius: 25px;
                font-weight: bold;
                font-size: 1.1rem;
                transition: transform 0.3s ease;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .footer {
                text-align: center;
                padding: 40px 0;
                border-top: 1px solid rgba(255,255,255,0.2);
                margin-top: 60px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💰 FinSplit</h1>
                <p>Split expenses effortlessly with friends and family. No more awkward money conversations or forgotten debts.</p>
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>🏠 Group Management</h3>
                    <p>Create pools for different groups - trips, roommates, office lunches, or any shared expenses. Organize your finances with ease.</p>
                </div>
                
                <div class="feature">
                    <h3>⚖️ Flexible Splitting</h3>
                    <p>Split equally, by percentage, or manually. Handle any expense scenario with our intelligent splitting algorithms.</p>
                </div>
                
                <div class="feature">
                    <h3>💳 UPI Integration</h3>
                    <p>Seamless payments with UPI integration. Settle up instantly with just a few clicks using your favorite payment app.</p>
                </div>
                
                <div class="feature">
                    <h3>📊 Smart Tracking</h3>
                    <p>Track all expenses, view balances, and get settlement suggestions. Never lose track of who owes what.</p>
                </div>
                
                <div class="feature">
                    <h3>🔒 Secure & Private</h3>
                    <p>Your financial data is secure with us. We use industry-standard encryption to protect your information.</p>
                </div>
                
                <div class="feature">
                    <h3>📱 Easy to Use</h3>
                    <p>Simple, intuitive interface that works on all devices. Add expenses, split bills, and settle up in seconds.</p>
                </div>
            </div>
            
            <div class="cta">
                <h2>Ready to Start Splitting?</h2>
                <p>Join thousands of users who trust FinSplit for their expense management.</p>
                <a href="#" class="btn">Get Started Free</a>
            </div>
            
            <div class="footer">
                <p>&copy; 2025 FinSplit. Split expenses easily with friends and family.</p>
                <p>Built with Django and deployed with Flask proxy for seamless experience.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/health')
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "FinSplit"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

