# WhatsApp Bulk Messenger

## Overview
A powerful WhatsApp web automation tool for sending bulk messages and managing communication efficiently.

## Features
- Initialize WhatsApp Web bot
- Send messages to single or multiple recipients
- Bulk messaging with CSV/Excel support
- Flexible phone number formatting
- Automatic message generation
- Comprehensive error handling and logging

## Prerequisites
- Python 3.8+
- Google Chrome
- ChromeDriver

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Yash0082/Whatsapp_MCP.git
cd Whatsapp_MCP
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Single Message Sending
1. Initialize the WhatsApp bot
2. Enter phone number(s)
3. Type your message
4. Click "Send"

### Bulk Messaging
1. Prepare a CSV/Excel file with phone numbers
   - Supports scientific notation
   - Automatically adds country code
   - Handles various number formats

2. Upload the file
3. Optionally provide a message
   - If no message is provided, it generates a default message using names

#### CSV File Format Examples:
```csv
phone_number,name,group
9.1885E+11,John Doe,Group A
9.19323E+11,Jane Smith,Group A
```

## Configuration
- Supports Indian phone numbers (country code 91)
- Automatically formats and validates phone numbers
- Generates default messages if none provided

## Logging
- Detailed logs in `logs/` directory
- Error screenshots in `error_images/`
- Tracking of message send status

## Troubleshooting
- Ensure Chrome is updated
- Check console logs for detailed error information
- Verify phone number format

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
[Specify your license here]

## Contact
[Your contact information] 