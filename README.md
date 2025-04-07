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
3. Enter your message
4. Click "Send Bulk Messages"

### CSV/Excel File Formats

The application supports multiple file formats and column names. Here are some examples:

#### Format 1: Standard Format
```csv
phone_number,name,group
919876543210,John Doe,Group A
919988776655,Jane Smith,Group B
```

#### Format 2: Different Column Names
```csv
mobile,customer_name,category
9876543210,John Doe,VIP
8899776655,Jane Smith,Regular
```

#### Format 3: Scientific Notation
```csv
contact,name
9.18849958013e11,Alice Cooper
9.19322612069e11,Bob Wilson
```

#### Format 4: Excel Format (.xlsx)
| phone | name | group |
|-------|------|-------|
| 919876543210 | John Doe | Group A |
| 919988776655 | Jane Smith | Group B |

#### Format 5: Mixed Number Formats
```csv
number,name,notes
08899776655,John,With leading zero
+919876543210,Jane,With plus sign
919988776655,Bob,Standard format
9.19876543210e11,Alice,Scientific notation
```

### Supported Column Names
The system automatically detects phone number columns with these names:
- phone
- phone_number
- mobile
- contact
- number
- tel
- telephone
- cell
- cellphone
- mobile_no
- contact_no
- mob
- mob_no

### Number Format Handling
The system automatically handles:
- 10-digit numbers (adds 91 prefix)
- Numbers with leading zeros
- Numbers with country code
- International format with '+'
- Scientific notation
- Numbers with spaces or special characters

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
- Check the error_images folder for screenshots of any failures

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