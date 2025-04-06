from app import app

if __name__ == "__main__":
    print("Starting WhatsApp Bulk Messaging Server...")
    print("Please wait for Chrome to open with WhatsApp Web...")
    app.run(debug=True, port=5000) 