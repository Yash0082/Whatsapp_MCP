from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from PIL import Image
import win32clipboard
from io import BytesIO
import subprocess
import platform

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Constants for tracking files
TRACKING_FOLDER = 'message_tracking'
MESSAGE_LOG_FILE = os.path.join(TRACKING_FOLDER, 'message_log.xlsx')

# Create tracking folder if it doesn't exist
os.makedirs(TRACKING_FOLDER, exist_ok=True)

def update_tracking_log(phone, message_type, content, status, error_message=""):
    """
    Update the tracking log with message details
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create new data entry
    new_data = {
        'timestamp': [timestamp],
        'phone': [phone],
        'type': [message_type],
        'content': [content],
        'status': [status],
        'error_message': [error_message]
    }
    
    try:
        # Try to read existing log
        if os.path.exists(MESSAGE_LOG_FILE):
            df = pd.read_excel(MESSAGE_LOG_FILE)
            new_df = pd.DataFrame(new_data)
            df = pd.concat([df, new_df], ignore_index=True)
        else:
            df = pd.DataFrame(new_data)
        
        # Save to Excel file
        df.to_excel(MESSAGE_LOG_FILE, index=False)
        return True
    except Exception as e:
        print(f"Error updating tracking log: {str(e)}")
        return False

def read_phone_numbers(file_path, group=None):
    """
    Read phone numbers from CSV/Excel file
    If group is specified, only return numbers from that group
    """
    try:
        # Determine file type from extension
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel.")

        # Filter by group if specified
        if group and 'group' in df.columns:
            df = df[df['group'] == group]

        # Return list of phone numbers
        return df['phone_number'].tolist()
    except Exception as e:
        print(f"Error reading phone numbers: {str(e)}")
        return None

def send_to_clipboard(image_path):
    """Helper function to copy image to clipboard"""
    try:
        print(f"Opening image from: {image_path}")
        image = Image.open(image_path)
        output = BytesIO()
        image.convert('RGB').save(output, 'BMP')
        data = output.getvalue()[14:]  # Remove header
        output.close()
        
        print("Opening clipboard...")
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        print("Image successfully copied to clipboard")
        return True
    except Exception as e:
        print(f"Error in send_to_clipboard: {str(e)}")
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        return False

class WhatsAppBot:
    def __init__(self):
        print("Initializing WhatsApp Bot...")
        self.driver = None
        self.wait = None

    def setup_driver(self):
        try:
            print("\n1. Setting up Chrome options...")
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            
            # Create profile directory if it doesn't exist
            profile_dir = os.path.join(os.getcwd(), 'chrome_profile')
            os.makedirs(profile_dir, exist_ok=True)
            chrome_options.add_argument(f'--user-data-dir={profile_dir}')
            
            print("2. Setting up Chrome driver...")
            try:
                # Check Chrome installation and version
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ]
                
                chrome_path = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_path = path
                        break
                
                if not chrome_path:
                    raise Exception("Chrome not found. Please install Google Chrome first.")
                
                # Get Chrome version
                version_cmd = f'wmic datafile where name="{chrome_path.replace("\\", "\\\\")}" get Version /value'
                version_output = subprocess.check_output(version_cmd, shell=True).decode()
                chrome_version = version_output.strip().split("=")[1].split(".")[0]
                print(f"Detected Chrome version: {chrome_version}")
                
                # Check if running in 64-bit Python
                is_64bits = platform.architecture()[0] == '64bit'
                
                # Configure ChromeDriverManager
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager(version=f"chrome_{chrome_version}").install()
                
                # Create service with specific binary location
                service = Service(
                    executable_path=driver_path,
                    log_path="chromedriver.log"  # Add logging
                )
                
            except Exception as e:
                print(f"Error setting up ChromeDriver: {str(e)}")
                print("Attempting to use local ChromeDriver...")
                
                # Try both chromedriver.exe and chromedriver-win64
                driver_paths = [
                    os.path.join(os.getcwd(), "chromedriver.exe"),
                    os.path.join(os.getcwd(), "chromedriver-win64", "chromedriver.exe")
                ]
                
                driver_found = False
                for path in driver_paths:
                    if os.path.exists(path):
                        print(f"Found local ChromeDriver at: {path}")
                        service = Service(
                            executable_path=path,
                            log_path="chromedriver.log"  # Add logging
                        )
                        driver_found = True
                        break
                
                if not driver_found:
                    raise Exception("ChromeDriver not found. Please download the correct version for your Chrome.")
            
            print("3. Starting Chrome browser...")
            try:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.wait = WebDriverWait(self.driver, 30)
            except Exception as e:
                print(f"Error starting Chrome: {str(e)}")
                print("This might be due to ChromeDriver version mismatch.")
                print("Please download ChromeDriver that matches your Chrome version from:")
                print("https://chromedriver.chromium.org/downloads")
                raise
            
            print("4. Opening WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")
            
            # Wait for WhatsApp Web to load
            print("Waiting for WhatsApp Web to load...")
            try:
                # Check for successful login or QR code
                self.wait.until(lambda driver: (
                    driver.find_elements(By.CSS_SELECTOR, 'div[title="Type a message"]') or
                    driver.find_elements(By.XPATH, '//div[@data-testid="qrcode"]')
                ))
                
                # Check which state we're in
                if self.driver.find_elements(By.CSS_SELECTOR, 'div[title="Type a message"]'):
                    print("Already logged in!")
                    return True
                else:
                    print("Please scan the QR code with your WhatsApp mobile app")
                    # Wait for successful login after QR scan
                    self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[title="Type a message"]'))
                    )
                    print("Successfully logged in!")
                    return True
                    
            except Exception as e:
                print(f"Error waiting for WhatsApp Web: {str(e)}")
                if self.driver:
                    self.driver.save_screenshot("error.png")
                return False
            
        except Exception as e:
            print(f"Error in setup_driver: {str(e)}")
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.save_screenshot("error.png")
                except:
                    pass
                self.driver.quit()
            return False

    def send_message(self, phone_number, message):
        try:
            # Format the URL with the phone number and message
            url = f"https://web.whatsapp.com/send?phone={phone_number}&text={message}"
            self.driver.get(url)
            
            # Wait for the send button to be clickable
            send_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]')))
            time.sleep(2)  # Small delay to ensure message is ready
            send_button.click()
            time.sleep(2)  # Wait for message to be sent
            
            # Update tracking log
            update_tracking_log(phone_number, "text", message, "success")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error sending message to {phone_number}: {error_msg}")
            # Update tracking log with error
            update_tracking_log(phone_number, "text", message, "failed", error_msg)
            return False

    def send_image(self, phone_number, image_path, caption=None):
        """Send an image with optional caption to a WhatsApp contact"""
        try:
            print(f"\nSending image to {phone_number}")
            
            # Validate image file
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Convert to absolute path and validate image
            abs_image_path = os.path.abspath(image_path)
            if not any(abs_image_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                raise ValueError("Unsupported image format. Use JPG, PNG, or GIF")
            
            # Open chat directly
            url = f"https://web.whatsapp.com/send?phone={phone_number}"
            self.driver.get(url)
            
            # Wait for chat to load
            print("Waiting for chat to load...")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[title="Type a message"]')))
            time.sleep(2)
            
            # Click attachment button
            print("Opening attachment menu...")
            attach_button = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-icon="attach-menu-plus"]'))
            )
            self.driver.execute_script("arguments[0].click();", attach_button)
            time.sleep(1)
            
            # Send image file
            print("Sending image...")
            file_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
            )
            file_input.send_keys(abs_image_path)
            time.sleep(2)
            
            # Add caption if provided
            if caption:
                print("Adding caption...")
                caption_box = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
                )
                caption_box.send_keys(caption)
                time.sleep(1)
            
            # Click send button
            print("Clicking send button...")
            send_button = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-icon="send"]'))
            )
            self.driver.execute_script("arguments[0].click();", send_button)
            time.sleep(2)
            
            print("Image sent successfully!")
            update_tracking_log(phone_number, "image", f"Image: {os.path.basename(image_path)}", "success")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error sending image: {error_msg}")
            if self.driver:
                self.driver.save_screenshot("error.png")
            update_tracking_log(phone_number, "image", f"Image: {os.path.basename(image_path)}", "failed", error_msg)
            return False

    def close(self):
        if self.driver:
            self.driver.quit()

    def send_message_to_multiple(self, phone_numbers, message):
        """Send a message to multiple phone numbers"""
        results = []
        for phone in phone_numbers:
            try:
                success = self.send_message(phone, message)
                results.append({
                    "phone": phone,
                    "status": "success" if success else "failed"
                })
            except Exception as e:
                results.append({
                    "phone": phone,
                    "status": "failed",
                    "error": str(e)
                })
        return results

# Initialize WhatsApp bot
whatsapp_bot = None

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhatsApp Bulk Messenger</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f0f2f5;
            }
            .container {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            h1 {
                color: #128C7E;
                text-align: center;
            }
            .button {
                background-color: #128C7E;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin: 10px 0;
                width: 100%;
            }
            .button:hover {
                background-color: #075E54;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                color: #333;
            }
            input[type="text"], input[type="file"], textarea {
                width: 100%;
                padding: 8px;
                margin-bottom: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            .status {
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
            }
            .success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .error {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .info {
                color: #666;
                font-size: 0.9em;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>WhatsApp Bulk Messenger</h1>
            
            <div class="form-group">
                <button id="initButton" class="button" onclick="initializeBot()">Initialize WhatsApp Bot</button>
                <div id="status"></div>
            </div>
            
            <form id="messageForm" onsubmit="event.preventDefault(); sendMessage();">
                <div class="form-group">
                    <label for="phone">Phone Numbers (comma-separated):</label>
                    <input type="text" id="phone" name="phone" placeholder="e.g., 919322612069, 919876543210" required>
                    <div class="info">Enter numbers without spaces, separated by commas. Country code (91 for India) followed by the 10-digit number.</div>
                </div>
                
                <div class="form-group">
                    <label for="message">Message (optional if sending image):</label>
                    <textarea id="message" name="message" placeholder="Enter your message"></textarea>
                </div>
                
                <div class="form-group">
                    <label for="image">Image (optional if sending message):</label>
                    <input type="file" id="image" name="image" accept="image/*">
                </div>
                
                <button type="submit" id="submitButton" class="button">Send</button>
                <div id="messageStatus"></div>
            </form>
            
            <div class="form-group" style="margin-top: 20px;">
                <form action="/send_message_bulk" method="post" enctype="multipart/form-data">
                    <label for="file">Upload CSV/Excel file for bulk messaging:</label>
                    <input type="file" id="file" name="file" accept=".csv,.xlsx,.xls" required>
                    <button type="submit" class="button">Send Bulk Messages</button>
                </form>
            </div>
        </div>
        
        <script>
            async function initializeBot() {
                const initButton = document.getElementById('initButton');
                const statusDiv = document.getElementById('status');
                
                initButton.disabled = true;
                initButton.textContent = 'Initializing...';
                statusDiv.textContent = 'Starting WhatsApp bot initialization...';
                statusDiv.className = 'status';
                
                try {
                    const response = await fetch('/init', {
                        method: 'POST'
                    });
                    const result = await response.json();
                    
                    if (result.success) {
                        statusDiv.textContent = 'Bot initialized successfully! Please check the Chrome window to scan the QR code.';
                        statusDiv.className = 'status success';
                    } else {
                        statusDiv.textContent = 'Failed to initialize bot: ' + result.message;
                        statusDiv.className = 'status error';
                        initButton.disabled = false;
                        initButton.textContent = 'Initialize WhatsApp Bot';
                    }
                } catch (error) {
                    statusDiv.textContent = 'Error: ' + error.message;
                    statusDiv.className = 'status error';
                    initButton.disabled = false;
                    initButton.textContent = 'Initialize WhatsApp Bot';
                }
            }
            
            async function sendMessage() {
                const form = document.getElementById('messageForm');
                const statusDiv = document.getElementById('messageStatus');
                const submitButton = document.getElementById('submitButton');
                const imageInput = document.getElementById('image');
                const messageInput = document.getElementById('message');
                
                // Check if at least one of message or image is provided
                if (!messageInput.value && !imageInput.files.length) {
                    statusDiv.textContent = 'Please provide either a message or an image';
                    statusDiv.className = 'status error';
                    return;
                }
                
                submitButton.disabled = true;
                statusDiv.textContent = 'Sending...';
                statusDiv.className = 'status';
                
                try {
                    const formData = new FormData(form);
                    const response = await fetch('/send_message', {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();
                    
                    if (result.success) {
                        statusDiv.textContent = 'Messages sent successfully!';
                        statusDiv.className = 'status success';
                        form.reset();
                    } else {
                        statusDiv.textContent = 'Failed to send: ' + result.message;
                        statusDiv.className = 'status error';
                    }
                } catch (error) {
                    statusDiv.textContent = 'Error: ' + error.message;
                    statusDiv.className = 'status error';
                }
                
                submitButton.disabled = false;
            }
        </script>
    </body>
    </html>
    '''

@app.route('/init', methods=['POST'])
def init_bot():
    global whatsapp_bot
    try:
        # Create a new bot instance if none exists or if driver is None
        if whatsapp_bot is None or whatsapp_bot.driver is None:
            print("\nInitializing new WhatsApp bot instance...")
            whatsapp_bot = WhatsAppBot()
            setup_success = whatsapp_bot.setup_driver()
            
            # Check if WhatsApp Web is actually loaded
            if setup_success and whatsapp_bot.driver:
                try:
                    # Additional check for WhatsApp Web elements
                    WebDriverWait(whatsapp_bot.driver, 5).until(lambda driver: (
                        driver.find_elements(By.CSS_SELECTOR, 'div[title="Type a message"]') or
                        driver.find_elements(By.XPATH, '//div[@data-testid="chat-list"]') or
                        driver.find_elements(By.XPATH, '//div[@data-testid="qrcode"]')
                    ))
                    return jsonify({"success": True, "message": "Bot initialized successfully"})
                except:
                    pass
            
            if whatsapp_bot.driver:
                whatsapp_bot.driver.save_screenshot("init_error.png")
            return jsonify({"success": False, "message": "Failed to initialize bot driver"})
        
        # Bot is already running, verify it's working
        try:
            WebDriverWait(whatsapp_bot.driver, 5).until(lambda driver: (
                driver.find_elements(By.CSS_SELECTOR, 'div[title="Type a message"]') or
                driver.find_elements(By.XPATH, '//div[@data-testid="chat-list"]')
            ))
            return jsonify({"success": True, "message": "Bot is already initialized"})
        except:
            # Bot exists but might be in a bad state
            if whatsapp_bot.driver:
                whatsapp_bot.driver.quit()
            whatsapp_bot = None
            return jsonify({"success": False, "message": "Bot needs to be reinitialized"})
        
    except Exception as e:
        print(f"Error initializing bot: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/send_message', methods=['POST'])
def send_message():
    global whatsapp_bot
    if not whatsapp_bot or whatsapp_bot.driver is None:
        return jsonify({"success": False, "message": "WhatsApp bot not initialized. Please initialize first."})
    
    try:
        # Get form data
        phone = request.form.get('phone')
        message = request.form.get('message', '')
        image = request.files.get('image')
        
        # Check if phone is a list of numbers (comma-separated)
        phone_numbers = [p.strip() for p in phone.split(',')] if phone else []
        
        # Validate input
        if not phone_numbers:
            return jsonify({"success": False, "message": "Phone number(s) are required"})
            
        if not message and not image:
            return jsonify({"success": False, "message": "Please provide either a message or an image"})
        
        # Process each phone number
        results = []
        for phone in phone_numbers:
            # Remove any spaces and ensure phone number format
            phone = phone.strip().replace(" ", "")
            if not phone.startswith("+"):
                phone = "+" + phone
                
            # If image is provided, send it
            if image:
                try:
                    # Create temp directory if it doesn't exist
                    temp_dir = 'temp_uploads'
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Save the image
                    image_path = os.path.join(temp_dir, image.filename)
                    image.save(image_path)
                    
                    # Send image with optional caption
                    success = whatsapp_bot.send_image(phone, image_path, message if message else None)
                    
                    # Clean up
                    os.remove(image_path)
                    
                    results.append({
                        "phone": phone,
                        "status": "success" if success else "failed",
                        "type": "image"
                    })
                    
                except Exception as e:
                    results.append({
                        "phone": phone,
                        "status": "failed",
                        "type": "image",
                        "error": str(e)
                    })
            else:
                # Send text message only
                success = whatsapp_bot.send_message(phone, message)
                results.append({
                    "phone": phone,
                    "status": "success" if success else "failed",
                    "type": "text"
                })
        
        # Check if all messages were sent successfully
        all_success = all(result["status"] == "success" for result in results)
        
        if all_success:
            return jsonify({
                "success": True,
                "message": "All messages sent successfully",
                "details": results
            })
        else:
            return jsonify({
                "success": False,
                "message": "Some messages failed to send",
                "details": results
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        })

@app.route('/send_image', methods=['POST'])
def send_image():
    global whatsapp_bot
    if not whatsapp_bot:
        return jsonify({"status": "error", "message": "WhatsApp bot not initialized"}), 400
    
    data = request.json
    phones = data.get('phones')  # Now expecting an array of phone numbers
    image_path = data.get('image_path')
    caption = data.get('caption', '')
    
    if not phones or not image_path:
        return jsonify({"status": "error", "message": "Phone numbers array and image path are required"}), 400
    
    if not isinstance(phones, list):
        return jsonify({"status": "error", "message": "Phones must be an array of phone numbers"}), 400
    
    results = []
    for phone in phones:
        success = whatsapp_bot.send_image(phone, image_path, caption)
        results.append({
            "phone": phone,
            "status": "success" if success else "failed"
        })
    
    # Check if all images were sent successfully
    all_success = all(result["status"] == "success" for result in results)
    
    if all_success:
        return jsonify({
            "status": "success",
            "message": "All images sent successfully",
            "details": results
        })
    else:
        return jsonify({
            "status": "partial_success" if any(result["status"] == "success" for result in results) else "error",
            "message": "Some or all images failed to send",
            "details": results
        }), 500

@app.route('/get_message_log', methods=['GET'])
def get_message_log():
    try:
        if os.path.exists(MESSAGE_LOG_FILE):
            df = pd.read_excel(MESSAGE_LOG_FILE)
            return jsonify({
                "status": "success",
                "data": df.to_dict('records')
            })
        else:
            return jsonify({
                "status": "success",
                "data": []
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error reading message log: {str(e)}"
        }), 500

@app.route('/send_message_bulk', methods=['POST'])
def send_message_bulk():
    global whatsapp_bot
    if not whatsapp_bot:
        return jsonify({"status": "error", "message": "WhatsApp bot not initialized"}), 400
    
    data = request.json
    file_path = data.get('file_path')  # Path to CSV/Excel file
    message = data.get('message')
    group = data.get('group', None)  # Optional group filter
    
    if not file_path or not message:
        return jsonify({"status": "error", "message": "File path and message are required"}), 400
    
    # Read phone numbers from file
    phones = read_phone_numbers(file_path, group)
    if not phones:
        return jsonify({"status": "error", "message": "Failed to read phone numbers from file"}), 400
    
    results = whatsapp_bot.send_message_to_multiple(phones, message)
    
    # Check if all messages were sent successfully
    all_success = all(result["status"] == "success" for result in results)
    
    if all_success:
        return jsonify({
            "status": "success",
            "message": "All messages sent successfully",
            "details": results
        })
    else:
        return jsonify({
            "status": "partial_success" if any(result["status"] == "success" for result in results) else "error",
            "message": "Some or all messages failed to send",
            "details": results
        }), 500

@app.route('/send_image_bulk', methods=['POST'])
def send_image_bulk():
    global whatsapp_bot
    if not whatsapp_bot:
        return jsonify({"status": "error", "message": "WhatsApp bot not initialized"}), 400
    
    data = request.json
    file_path = data.get('file_path')  # Path to CSV/Excel file
    image_path = data.get('image_path')
    caption = data.get('caption', '')
    group = data.get('group', None)  # Optional group filter
    
    if not file_path or not image_path:
        return jsonify({"status": "error", "message": "File path and image path are required"}), 400
    
    # Read phone numbers from file
    phones = read_phone_numbers(file_path, group)
    if not phones:
        return jsonify({"status": "error", "message": "Failed to read phone numbers from file"}), 400
    
    results = whatsapp_bot.send_message_to_multiple(phones, caption)
    
    # Check if all images were sent successfully
    all_success = all(result["status"] == "success" for result in results)
    
    if all_success:
        return jsonify({
            "status": "success",
            "message": "All images sent successfully",
            "details": results
        })
    else:
        return jsonify({
            "status": "partial_success" if any(result["status"] == "success" for result in results) else "error",
            "message": "Some or all images failed to send",
            "details": results
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 