from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Import database functions (this might fail if DATABASE_URL is not set)
try:
    from database import (
        store_user_integration_data, 
        get_user_integration_data, 
        delete_user_integration_data,
        test_database_connection,
        get_user_count
    )
    from notion_helper import NotionAPIHelper, validate_database_schema
    
    # Test database connection on startup
    if test_database_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed on startup")
        
except Exception as e:
    logger.error(f"❌ Failed to import database modules: {e}")
    # Define dummy functions so the app doesn't crash
    def store_user_integration_data(*args, **kwargs):
        raise Exception("Database not connected")
    def get_user_integration_data(*args, **kwargs):
        return None
    def delete_user_integration_data(*args, **kwargs):
        return False
    def test_database_connection():
        return False
    def get_user_count():
        return 0

@app.route('/')
def index():
    """Home page with basic information"""
    user_count = get_user_count()
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram-Notion Setup Assistant</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .stats { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .button { background: #0070f3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 5px; }
            .button:hover { background: #0051cc; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }
            .feature { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #0070f3; }
            .footer { text-align: center; margin-top: 40px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Telegram-Notion Setup Assistant</h1>
                <p>Connect your Telegram bot to Notion with guided setup</p>
            </div>
            
            <div class="stats">
                <strong>📊 Active Users:</strong> {{ user_count }} connected integrations
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>🔧 Easy Setup</h3>
                    <p>Step-by-step guided process to connect your Notion workspace</p>
                </div>
                <div class="feature">
                    <h3>🔒 Secure</h3>
                    <p>Your integration tokens are stored securely and encrypted</p>
                </div>
                <div class="feature">
                    <h3>⚡ Instant</h3>
                    <p>No approval process - start using immediately</p>
                </div>
                <div class="feature">
                    <h3>🎯 Smart Tasks</h3>
                    <p>AI-powered task creation from text, voice, and images</p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <h3>Get Started</h3>
                <p>Go to your Telegram bot and type <code>/setup</code> to begin!</p>
            </div>
            
            <div class="footer">
                <p>Powered by Flask • Notion API • PostgreSQL</p>
            </div>
        </div>
    </body>
    </html>
    """, user_count=user_count)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    db_status = test_database_connection()
    return jsonify({
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "users": get_user_count(),
        "service": "telegram-notion-setup-assistant"
    })

@app.route('/setup/<int:telegram_id>')
def setup_page(telegram_id):
    """Setup instructions and form page"""
    # Check if user already has integration
    existing_user = get_user_integration_data(telegram_id)
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Notion Integration Setup</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; line-height: 1.6; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .step { background: #f8f9fa; margin: 20px 0; padding: 20px; border-radius: 8px; border-left: 4px solid #0070f3; }
            .step h3 { margin-top: 0; color: #0070f3; }
            .form-group { margin: 15px 0; }
            .form-group label { display: block; font-weight: bold; margin-bottom: 5px; }
            .form-group input, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
            .button { background: #0070f3; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            .button:hover { background: #0051cc; }
            .alert { padding: 15px; margin: 20px 0; border-radius: 5px; }
            .alert-info { background: #e3f2fd; border-left: 4px solid #2196f3; }
            .alert-success { background: #e8f5e8; border-left: 4px solid #4caf50; }
            .alert-warning { background: #fff3e0; border-left: 4px solid #ff9800; }
            ol li { margin: 8px 0; }
            code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
            .existing-user { background: #e8f5e8; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔗 Set Up Your Notion Integration</h1>
                <p><strong>Telegram ID:</strong> {{ telegram_id }}</p>
            </div>
            
            {% if existing_user %}
            <div class="existing-user">
                <h3>✅ Integration Already Configured</h3>
                <p><strong>Workspace:</strong> {{ existing_user.notion_workspace_name }}</p>
                <p><strong>Connected:</strong> {{ existing_user.created_at.strftime('%Y-%m-%d %H:%M') }}</p>
                <p>Your integration is working! You can create tasks in Telegram.</p>
                <form method="post" action="{{ url_for('disconnect_user', telegram_id=telegram_id) }}" style="margin-top: 15px;">
                    <button type="submit" class="button" style="background: #dc3545;" onclick="return confirm('Are you sure you want to disconnect?')">
                        Disconnect Integration
                    </button>
                </form>
            </div>
            {% endif %}
            
            <div class="step">
                <h3>📋 Before You Start</h3>
                <p>Make sure you have a Notion database with these exact properties:</p>
                <ul>
                    <li><strong>Name</strong> (Title)</li>
                    <li><strong>Start at</strong> (Date)</li>
                    <li><strong>Finish at</strong> (Date)</li>
                    <li><strong>Priority</strong> (Multi-select: Urgent, High, Long-term)</li>
                    <li><strong>Progress</strong> (Status: Not Started, Doing, Paused, Done)</li>
                </ul>
                <p>Need help? <a href="https://www.notion.so/templates/task-database" target="_blank">Use this Notion template</a></p>
            </div>
            
            <div class="step">
                <h3>Step 1: Create Internal Integration</h3>
                <ol>
                    <li>Go to <a href="https://www.notion.so/profile/integrations" target="_blank">Notion Integrations</a></li>
                    <li>Click <strong>"New Integration"</strong></li>
                    <li>Choose <strong>"Internal"</strong> (not Public)</li>
                    <li>Name: <code>Telegram Task Manager</code></li>
                    <li>Select your workspace</li>
                    <li>Click <strong>"Submit"</strong></li>
                </ol>
            </div>
            
            <div class="step">
                <h3>Step 2: Copy Integration Token</h3>
                <ol>
                    <li>In your integration page, find the <strong>"Internal Integration Token"</strong></li>
                    <li>Click <strong>"Show"</strong> then <strong>"Copy"</strong></li>
                    <li>The token starts with <code>secret_</code></li>
                </ol>
            </div>
            
            <div class="step">
                <h3>Step 3: Share Your Database</h3>
                <ol>
                    <li>Go to your Notion task database</li>
                    <li>Click the <strong>"..."</strong> menu (top right)</li>
                    <li>Select <strong>"Add connections"</strong></li>
                    <li>Find and select <strong>"Telegram Task Manager"</strong></li>
                    <li>Click <strong>"Confirm"</strong></li>
                </ol>
            </div>
            
            <div class="step">
                <h3>Step 4: Complete Setup</h3>
                <form method="post" action="{{ url_for('verify_setup', telegram_id=telegram_id) }}">
                    <div class="form-group">
                        <label for="token">Integration Token:</label>
                        <input type="text" id="token" name="token" placeholder="secret_..." required>
                        <small>Paste the token from your Notion integration</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="database_id">Database ID:</label>
                        <input type="text" id="database_id" name="database_id" placeholder="32-character database ID" required>
                        <small>Copy from your database URL: notion.so/workspace/DATABASE_ID?v=...</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="user_name">Your Name (optional):</label>
                        <input type="text" id="user_name" name="user_name" placeholder="Your name">
                    </div>
                    
                    <button type="submit" class="button">🚀 Complete Setup</button>
                </form>
            </div>
            
            <div class="alert alert-info">
                <strong>💡 Need Help?</strong> If you encounter issues, check that:
                <ul>
                    <li>Your database has all required properties</li>
                    <li>You copied the full integration token</li>
                    <li>You shared the database with your integration</li>
                    <li>Database ID is the 32-character code from the URL</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """, telegram_id=telegram_id, existing_user=existing_user)

@app.route('/verify/<int:telegram_id>', methods=['POST'])
def verify_setup(telegram_id):
    """Verify and store integration details"""
    token = request.form.get('token', '').strip()
    database_id = request.form.get('database_id', '').strip()
    user_name = request.form.get('user_name', '').strip()
    
    # Basic validation
    if not token or not database_id:
        flash('Please provide both integration token and database ID', 'error')
        return redirect(url_for('setup_page', telegram_id=telegram_id))
    
    if not token.startswith('secret_'):
        flash('Integration token should start with "secret_"', 'error')
        return redirect(url_for('setup_page', telegram_id=telegram_id))
    
    try:
        # Test Notion connection
        notion_helper = NotionAPIHelper(token)
        
        # Test basic connection
        connection_success, user_info = notion_helper.test_connection()
        if not connection_success:
            flash(f'Invalid integration token: {user_info}', 'error')
            return redirect(url_for('setup_page', telegram_id=telegram_id))
        
        # Test database access
        db_success, database_info = notion_helper.get_database_info(database_id)
        if not db_success:
            flash(f'Cannot access database. Please check the database ID and ensure your integration has access to it.', 'error')
            return redirect(url_for('setup_page', telegram_id=telegram_id))
        
        # Validate database schema
        missing_props, incorrect_types = validate_database_schema(database_info)
        if missing_props or incorrect_types:
            error_msg = "Database schema issues found:\n"
            if missing_props:
                error_msg += f"Missing properties: {', '.join(missing_props)}\n"
            if incorrect_types:
                error_msg += f"Incorrect property types: {', '.join(incorrect_types)}"
            flash(error_msg, 'error')
            return redirect(url_for('setup_page', telegram_id=telegram_id))
        
        # Test write access by creating a test page
        test_success, test_result = notion_helper.create_test_page(database_id)
        if not test_success:
            flash(f'Cannot create pages in database. Please ensure your integration has write access.', 'error')
            return redirect(url_for('setup_page', telegram_id=telegram_id))
        
        # Store integration data
        integration_data = {
            'access_token': token,
            'workspace_id': database_info.get('id', 'unknown'),
            'workspace_name': user_info.get('name', 'Personal Workspace'),
            'bot_id': 'internal_integration',
            'database_id': database_id,
            'user_name': user_name if user_name else user_info.get('name', 'Unknown')
        }
        
        store_user_integration_data(telegram_id, integration_data)
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Setup Complete!</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; text-align: center; }
                .container { max-width: 600px; margin: 50px auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .success { color: #4caf50; font-size: 48px; margin-bottom: 20px; }
                .details { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: left; }
                .button { background: #0070f3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 10px; }
                .button:hover { background: #0051cc; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✅</div>
                <h1>Setup Complete!</h1>
                <p>Your Notion integration is now connected and working perfectly.</p>
                
                <div class="details">
                    <h3>📋 Connection Details:</h3>
                    <p><strong>User:</strong> {{ user_name }}</p>
                    <p><strong>Workspace:</strong> {{ workspace_name }}</p>
                    <p><strong>Database:</strong> {{ database_title }}</p>
                    <p><strong>Test Page:</strong> Created successfully ✅</p>
                </div>
                
                <h3>🚀 Next Steps:</h3>
                <ol style="text-align: left; max-width: 400px; margin: 0 auto;">
                    <li>Return to your Telegram bot</li>
                    <li>Try sending a message like "Buy groceries tomorrow"</li>
                    <li>Check your Notion database for the new task!</li>
                    <li>You can also send voice messages and images</li>
                </ol>
                
                <p style="margin-top: 30px;">
                    <strong>You can now close this window and return to Telegram.</strong>
                </p>
                
                <div style="margin-top: 40px; color: #666; font-size: 14px;">
                    <p>Need help? Contact support or check the documentation.</p>
                </div>
            </div>
        </body>
        </html>
        """, 
        user_name=integration_data['user_name'],
        workspace_name=integration_data['workspace_name'],
        database_title=database_info.get('title', [{}])[0].get('text', {}).get('content', 'Your Database')
        )
        
    except Exception as e:
        logger.error(f"Setup verification error for user {telegram_id}: {str(e)}")
        flash(f'Setup failed: {str(e)}', 'error')
        return redirect(url_for('setup_page', telegram_id=telegram_id))

@app.route('/api/user/<int:telegram_id>')
def get_user_data(telegram_id):
    """API endpoint for Raspberry Pi to get user integration data"""
    try:
        user_data = get_user_integration_data(telegram_id)
        
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "telegram_id": telegram_id,
            "access_token": user_data['notion_access_token'],
            "workspace_id": user_data['notion_workspace_id'],
            "workspace_name": user_data['notion_workspace_name'],
            "bot_id": user_data['notion_bot_id'],
            "database_id": user_data['notion_database_id'],
            "user_name": user_data['user_name'],
            "connected_at": user_data['created_at'].isoformat(),
            "updated_at": user_data['updated_at'].isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting user data for {telegram_id}: {e}")
        return jsonify({"error": "Failed to get user data"}), 500

@app.route('/disconnect/<int:telegram_id>', methods=['POST'])
def disconnect_user(telegram_id):
    """Disconnect a user (delete integration data)"""
    try:
        success = delete_user_integration_data(telegram_id)
        
        if not success:
            flash('User not found or already disconnected', 'error')
        else:
            flash('Integration disconnected successfully', 'success')
            
        return redirect(url_for('setup_page', telegram_id=telegram_id))
        
    except Exception as e:
        logger.error(f"Error disconnecting user {telegram_id}: {e}")
        flash('Failed to disconnect integration', 'error')
        return redirect(url_for('setup_page', telegram_id=telegram_id))

@app.route('/api/user/<int:telegram_id>', methods=['DELETE'])
def api_disconnect_user(telegram_id):
    """API endpoint to disconnect a user"""
    try:
        success = delete_user_integration_data(telegram_id)
        
        if not success:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({"success": True, "message": "User disconnected successfully"})
        
    except Exception as e:
        logger.error(f"Error disconnecting user {telegram_id}: {e}")
        return jsonify({"error": "Failed to disconnect user"}), 500

@app.route('/debug/env')
def debug_env():
    """Debug endpoint to check environment variables"""
    if not app.debug:  # Only allow in development
        return "Debug endpoint disabled in production", 403
    
    import os
    env_vars = {
        'DATABASE_URL': os.getenv('DATABASE_URL', 'NOT SET')[:50] + '...' if os.getenv('DATABASE_URL') else 'NOT SET',
        'POSTGRES_URL': os.getenv('POSTGRES_URL', 'NOT SET'),
        'PGURL': os.getenv('PGURL', 'NOT SET'),
        'FLASK_SECRET_KEY': 'SET' if os.getenv('FLASK_SECRET_KEY') else 'NOT SET',
        'All DB-related vars': [k for k in os.environ.keys() if any(term in k.upper() for term in ['DATA', 'PG', 'POSTGRES', 'DB'])]
    }
    
    return jsonify(env_vars)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template_string("""
    <html><body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="{{ url_for('index') }}">← Go Home</a>
    </body></html>
    """), 404

@app.errorhandler(500)
def internal_error(error):
   return render_template_string("""
   <html><body style="font-family: Arial; text-align: center; padding: 50px;">
       <h1>500 - Internal Server Error</h1>
       <p>Something went wrong on our end.</p>
       <a href="{{ url_for('index') }}">← Go Home</a>
   </body></html>
   """), 500

if __name__ == '__main__':
   app.run(debug=False, host='0.0.0.0', port=5000)
