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
import subprocess
import platform
import uuid

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Constants for tracking files
TRACKING_FOLDER = 'message_tracking'
MESSAGE_LOG_FILE = os.path.join(TRACKING_FOLDER, 'message_log.xlsx')

# Constants for file storage
UPLOAD_FOLDER = 'uploaded_images'
TEMP_FOLDER = 'temp_uploads'
ERROR_FOLDER = 'error_images'
LOGS_FOLDER = 'logs'

# Create necessary directories
for folder in [TRACKING_FOLDER, UPLOAD_FOLDER, TEMP_FOLDER, ERROR_FOLDER, LOGS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

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

def save_uploaded_image(file):
    """Save uploaded image with a unique filename"""
    try:
        if not file:
            print("No file provided")
            return None
            
        # Generate unique filename
        original_filename = file.filename
        if not original_filename:
            print("No filename provided")
            return None
            
        file_ext = os.path.splitext(original_filename)[1].lower()
        if not file_ext:
            print("No file extension found")
            return None
            
        # Check if extension is allowed
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
        if file_ext not in allowed_extensions:
            print(f"Invalid file extension: {file_ext}")
            return None
            
        # Create unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Ensure upload folder exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            print(f"Created upload folder: {UPLOAD_FOLDER}")
        
        # Save in upload folder with absolute path
        save_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, unique_filename))
        print(f"Attempting to save file to: {save_path}")
        
        # Save the file
        file.save(save_path)
        
        # Verify file was saved
        if os.path.exists(save_path):
            print(f"Successfully saved image as: {save_path}")
            return save_path
        else:
            print("File was not saved successfully")
            return None
            
    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return None

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
                    log_path=os.path.join("logs", "chromedriver.log")
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
                            log_path=os.path.join("logs", "chromedriver.log")
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
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    self.driver.save_screenshot(os.path.join("error_images", f"init_error_{timestamp}.png"))
                return False
            
        except Exception as e:
            print(f"Error in setup_driver: {str(e)}")
            if hasattr(self, 'driver') and self.driver:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    self.driver.save_screenshot(os.path.join("error_images", f"setup_error_{timestamp}.png"))
                except:
                    pass
                self.driver.quit()
            return False

    def send_message(self, phone, message):
        try:
            # Format the URL with the phone number and message
            url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
            self.driver.get(url)
            
            # Wait for the send button to be clickable
            send_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]')))
            time.sleep(2)  # Small delay to ensure message is ready
            send_button.click()
            time.sleep(2)  # Wait for message to be sent
            
            # Update tracking log
            update_tracking_log(phone, "text", message, "success")
            return True
            
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            if self.driver:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.driver.save_screenshot(os.path.join("error_images", f"message_error_{timestamp}.png"))
            return False

    def send_image(self, phone, image_path, caption=None):
        """Send an image to a WhatsApp contact with optional caption"""
        try:
            print(f"\nAttempting to send image to {phone}")
            
            # Open chat with the phone number
            url = f"https://web.whatsapp.com/send?phone={phone}"
            print(f"Opening URL: {url}")
            self.driver.get(url)
            
            # Wait for chat to load
            print("Waiting for chat to load...")
            time.sleep(5)  # Ensure chat is fully loaded
            
            # Search for the chat (in case direct URL doesn't work)
            try:
                search_box = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
                )
                search_box.click()
                search_box.send_keys(phone)
                time.sleep(2)
                search_box.send_keys(Keys.ENTER)
            except Exception as e:
                print(f"Error searching for chat: {str(e)}")
            
            # Wait for chat to be ready
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[title="Type a message"]')))
            time.sleep(2)
            
            # Attach file
            try:
                # Try multiple attachment button selectors
                attachment_selectors = [
                    "//span[@data-icon='clip']",
                    "//span[@data-testid='attach-menu']",
                    "//span[@data-testid='attach-menu-plus']"
                ]
                
                attachment_btn = None
                for selector in attachment_selectors:
                    try:
                        attachment_btn = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        print(f"Found attachment button with selector: {selector}")
                        break
                    except:
                        continue
                
                if not attachment_btn:
                    raise Exception("Could not find attachment button")
                
                attachment_btn.click()
                time.sleep(1)
            except Exception as e:
                print(f"Error clicking attachment button: {str(e)}")
                raise
            
            # Input image
            try:
                image_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@accept='image/*,video/mp4,video/3gpp,video/quicktime']"))
                )
                abs_image_path = os.path.abspath(image_path)
                print(f"Uploading image from: {abs_image_path}")
                image_input.send_keys(abs_image_path)
            except Exception as e:
                print(f"Error uploading image: {str(e)}")
                raise
            
            # Wait for image preview
            time.sleep(3)
            
            # Add caption if provided
            if caption:
                try:
                    # Try multiple caption box selectors
                    caption_selectors = [
                        "//div[@contenteditable='true'][@data-tab='6']",
                        "//div[@contenteditable='true'][contains(@data-testid, 'media-caption-input')]"
                    ]
                    
                    caption_box = None
                    for selector in caption_selectors:
                        try:
                            caption_box = self.wait.until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            print(f"Found caption box with selector: {selector}")
                            break
                        except:
                            continue
                    
                    if caption_box:
                        caption_box.clear()
                        caption_box.send_keys(caption)
                        time.sleep(1)
                except Exception as e:
                    print(f"Error adding caption: {str(e)}")
            
            # Send image
            try:
                # Try multiple send button selectors
                send_selectors = [
                    "//span[@data-icon='send']",
                    "//span[@data-testid='send']"
                ]
                
                send_button = None
                for selector in send_selectors:
                    try:
                        send_button = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        print(f"Found send button with selector: {selector}")
                        break
                    except:
                        continue
                
                if not send_button:
                    raise Exception("Could not find send button")
                
                send_button.click()
            except Exception as e:
                print(f"Error sending image: {str(e)}")
                raise
            
            # Wait for message to be sent
            time.sleep(3)
            
            print("Image sent successfully!")
            update_tracking_log(phone, "image", f"Image: {os.path.basename(image_path)}", "success")
            return True
            
        except Exception as e:
            print(f"Error sending image: {str(e)}")
            if self.driver:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                error_screenshot = os.path.join("error_images", f"image_error_{timestamp}.png")
                self.driver.save_screenshot(error_screenshot)
                print(f"Error screenshot saved to: {error_screenshot}")
            update_tracking_log(phone, "image", f"Image: {os.path.basename(image_path)}", "failed", str(e))
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
                    <label for="message">Message:</label>
                    <textarea id="message" name="message" placeholder="Enter your message" required></textarea>
                </div>
                
                <button type="submit" id="submitButton" class="button">Send</button>
                <div id="messageStatus"></div>
            </form>
            
            <div class="form-group" style="margin-top: 20px;">
                <form action="/send_message_bulk" method="post" enctype="multipart/form-data">
                    <label for="file">Upload CSV/Excel file for bulk messaging:</label>
                    <input type="file" id="file" name="file" accept=".csv,.xlsx,.xls" required>
                    <div class="form-group">
                        <label for="bulk_message">Message for bulk sending:</label>
                        <textarea id="bulk_message" name="message" placeholder="Enter your message" required></textarea>
                    </div>
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
                const messageInput = document.getElementById('message');
                
                // Check if message is provided
                if (!messageInput.value) {
                    statusDiv.textContent = 'Please provide a message';
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
        whatsapp_bot = WhatsAppBot()
        success = whatsapp_bot.setup_driver()
        if success:
            return jsonify({"success": True, "message": "WhatsApp bot initialized successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to initialize WhatsApp bot"})
    except Exception as e:
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
        
        print(f"Received request - Phone: {phone}")
        
        # Check if phone is a list of numbers (comma-separated)
        phone_numbers = [p.strip() for p in phone.split(',')] if phone else []
        
        # Validate input
        if not phone_numbers:
            return jsonify({"success": False, "message": "Phone number(s) are required"})
            
        if not message:
            return jsonify({"success": False, "message": "Message is required"})
        
        # Process each phone number
        results = []
        
        for phone in phone_numbers:
            # Remove any spaces and ensure phone number format
            phone = phone.strip().replace(" ", "")
            if not phone.startswith("+"):
                phone = "+" + phone
            
            try:
                # Send text message
                success = whatsapp_bot.send_message(phone, message)
                results.append({
                    "phone": phone,
                    "status": "success" if success else "failed",
                    "type": "text"
                })
            except Exception as e:
                error_msg = str(e)
                print(f"Error sending to {phone}: {error_msg}")
                results.append({
                    "phone": phone,
                    "status": "failed",
                    "error": error_msg,
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
        error_msg = str(e)
        print(f"Error in send_message route: {error_msg}")
        return jsonify({
            "success": False,
            "message": f"Error: {error_msg}"
        })

def find_phone_column(df):
    """
    Find the column containing phone numbers in the DataFrame
    Returns the name of the column containing phone numbers
    """
    # Common column names for phone numbers
    phone_columns = [
        'phone', 'phone_number', 'mobile', 'contact', 'number', 'tel',
        'telephone', 'cell', 'cellphone', 'phone no', 'mobile no',
        'contact no', 'mob', 'mob_no', 'mobile_number'
    ]
    
    # First, check for exact matches in column names
    for col in df.columns:
        if col.lower().replace(' ', '_') in phone_columns:
            return col
    
    # If no exact match, try to find a column with numeric values
    for col in df.columns:
        # Check if the column contains numbers (allowing for scientific notation)
        if df[col].dtype in ['int64', 'float64'] or \
           (df[col].dtype == 'object' and df[col].str.contains(r'^\d+$|^\d+\.\d+e\+\d+$', na=True).any()):
            return col
    
    # If still no match, return the first column as default
    return df.columns[0]

def format_phone_number(number):
    """
    Convert phone number to standard format
    - Handles scientific notation
    - Ensures country code is present
    - Removes any non-digit characters
    """
    try:
        # Handle NaN or empty values
        if pd.isna(number) or str(number).strip() == '':
            return None
            
        # Convert to string and handle scientific notation
        if isinstance(number, float):
            str_number = f"{float(number):.0f}"
        else:
            str_number = str(number)
        
        # Remove any non-digit characters
        digits_only = ''.join(filter(str.isdigit, str_number))
        
        # Handle different formats
        if len(digits_only) <= 10:  # Only local number
            digits_only = '91' + digits_only.zfill(10)
        elif len(digits_only) > 12:  # Too many digits
            digits_only = digits_only[-12:]  # Take last 12 digits
        elif len(digits_only) == 11 and digits_only.startswith('0'):  # Remove leading 0
            digits_only = '91' + digits_only[1:]
        elif len(digits_only) == 12 and not digits_only.startswith('91'):  # Wrong country code
            digits_only = '91' + digits_only[-10:]
        
        # Validate final number
        if len(digits_only) == 12 and digits_only.startswith('91'):
            return digits_only
        return None
        
    except Exception as e:
        print(f"Error formatting phone number {number}: {str(e)}")
        return None

@app.route('/send_message_bulk', methods=['POST'])
def send_message_bulk():
    global whatsapp_bot
    if not whatsapp_bot or whatsapp_bot.driver is None:
        return jsonify({"success": False, "message": "WhatsApp bot not initialized. Please initialize first."})
    
    try:
        # Debug: Print all form data and files
        print("Form Data:", request.form)
        print("Files:", request.files)
        
        # Get the uploaded file
        file = request.files.get('file')
        if not file:
            print("No file uploaded")
            return jsonify({"success": False, "message": "No file uploaded"})
        
        # Save the file temporarily
        temp_dir = 'temp_uploads'
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        
        # Read the file
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                print(f"Unsupported file format: {file.filename}")
                return jsonify({"success": False, "message": "Unsupported file format"})
            
            # Debug: Print DataFrame info
            print("DataFrame Columns:", df.columns)
            print("DataFrame Head:\n", df.head())
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return jsonify({"success": False, "message": f"Error reading file: {str(e)}"})
        
        # Validate DataFrame
        if df.empty or len(df.columns) == 0:
            print("File is empty or has no columns")
            return jsonify({"success": False, "message": "File is empty or has no columns"})
        
        # Find and extract phone numbers
        try:
            # Find the column containing phone numbers
            phone_column = find_phone_column(df)
            print(f"Using column '{phone_column}' for phone numbers")
            
            # Format phone numbers
            phones = []
            invalid_numbers = []
            
            for idx, number in enumerate(df[phone_column]):
                formatted_number = format_phone_number(number)
                if formatted_number:
                    phones.append(formatted_number)
                else:
                    invalid_numbers.append(f"Row {idx + 2}: {number}")  # +2 because idx starts at 0 and we skip header
            
            print(f"Extracted {len(phones)} valid phone numbers")
            if invalid_numbers:
                print(f"Found {len(invalid_numbers)} invalid numbers:")
                for num in invalid_numbers:
                    print(f"  - {num}")
            
            if not phones:
                print("No valid phone numbers found")
                return jsonify({
                    "success": False,
                    "message": "No valid phone numbers found",
                    "details": {
                        "invalid_numbers": invalid_numbers
                    }
                })
                
        except Exception as e:
            print(f"Error extracting phone numbers: {str(e)}")
            return jsonify({"success": False, "message": f"Error extracting phone numbers: {str(e)}"})
        
        # Get message from form
        message = request.form.get('message', '').strip()
        print(f"Message from form: {message}")
        
        # Validate message
        if not message:
            return jsonify({"success": False, "message": "Message is required"})
        
        print(f"Final message to be sent: {message}")
        
        # Send messages to all phone numbers
        results = whatsapp_bot.send_message_to_multiple(phones, message)
        
        # Clean up
        os.remove(file_path)
        
        # Check if all messages were sent successfully
        all_success = all(result["status"] == "success" for result in results)
        
        # Include information about invalid numbers in the response
        response = {
            "success": all_success,
            "message": "All messages sent successfully" if all_success else "Some messages failed to send",
            "details": {
                "results": results,
                "invalid_numbers": invalid_numbers if invalid_numbers else []
            }
        }
        
        return jsonify(response)
            
    except Exception as e:
        print(f"Unexpected error in send_message_bulk: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        })

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

if __name__ == '__main__':
    app.run(debug=True, port=5000) 