# WhatsApp Bulk Messaging Server

A Flask-based server that allows you to send bulk messages and images through WhatsApp Web using Selenium automation.

## Prerequisites

- Python 3.13.2
- Google Chrome browser installed
- Active WhatsApp account
- Internet connection

## Setup

1. Create and activate virtual environment:
```bash
python -m venv mcp_whatsapp_env
.\mcp_whatsapp_env\Scripts\Activate.ps1  # For Windows PowerShell
```

2. Install required packages:
```bash
pip install selenium webdriver-manager python-dotenv flask pandas openpyxl
```

3. Run the server:
```bash
python app.py
```

4. When you first initialize the bot, you'll need to scan the WhatsApp Web QR code with your phone.

## API Endpoints

### 1. Initialize Bot
```http
POST /init
```
Initializes the WhatsApp bot and opens WhatsApp Web for QR code scanning.

### 2. Send Bulk Messages
```http
POST /send_message
Content-Type: application/json

{
    "phones": ["911234567890", "911234567891", "911234567892"],  # Array of phone numbers
    "message": "Your message here"
}
```

Response:
```json
{
    "status": "success",  # or "partial_success" or "error"
    "message": "All messages sent successfully",
    "details": [
        {"phone": "911234567890", "status": "success"},
        {"phone": "911234567891", "status": "success"},
        {"phone": "911234567892", "status": "failed"}
    ]
}
```

### 3. Send Bulk Images
```http
POST /send_image
Content-Type: application/json

{
    "phones": ["911234567890", "911234567891", "911234567892"],  # Array of phone numbers
    "image_path": "path/to/your/image.jpg",
    "caption": "Optional image caption"  # Optional
}
```

Response:
```json
{
    "status": "success",  # or "partial_success" or "error"
    "message": "All images sent successfully",
    "details": [
        {"phone": "911234567890", "status": "success"},
        {"phone": "911234567891", "status": "success"},
        {"phone": "911234567892", "status": "failed"}
    ]
}
```

### 4. Get Message Log
```http
GET /get_message_log
```

Returns the complete message sending history in JSON format. The log includes:
- Timestamp of each message
- Phone number
- Message type (text/image)
- Content
- Status (success/failed)
- Error message (if any)

## Message Tracking

The server maintains a detailed log of all message attempts in an Excel file:

- Location: `message_tracking/message_log.xlsx`
- Format: Excel spreadsheet
- Columns:
  - timestamp: When the message was sent
  - phone: Recipient's phone number
  - type: Message type (text/image)
  - content: Message content or image path
  - status: Success or failure
  - error_message: Details if sending failed

The log is automatically updated after each message attempt, whether successful or failed.

## Important Notes

1. Phone numbers should include country code without '+' or '00' (e.g., "911234567890" for India)
2. The server maintains a Chrome session, so you only need to scan QR code once
3. Keep the browser window open while sending messages
4. The server runs on http://localhost:5000 by default
5. For bulk messaging, the server will attempt to send to all numbers even if some fail
6. The response includes detailed status for each phone number
7. All message attempts are logged in the Excel file for tracking and auditing

## Error Handling

- The server will return appropriate error messages if:
  - WhatsApp bot is not initialized
  - Required parameters are missing
  - Message or image sending fails
  - Invalid phone number format
  - Phones parameter is not an array

## Security Considerations

- This server is intended for local use only
- Don't expose it to the public internet without proper security measures
- Keep your WhatsApp session secure
- Don't share your QR code or session data
- Regularly backup your message tracking logs 