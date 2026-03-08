import win32com.client
import pythoncom
import traceback
import logging

logger = logging.getLogger(__name__)

class OutlookEngine:
    def __init__(self):
        pass

    def test_connection(self):
        try:
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            # 6 is the inbox folder
            inbox = namespace.GetDefaultFolder(6)
            account_name = str(namespace.Accounts.Item(1)) if namespace.Accounts.Count > 0 else "Unknown"
            
            return {
                "success": True,
                "message": f"Successfully connected to Outlook. Primary account: {account_name}"
            }
        except Exception as e:
            logger.error(f"Outlook connection failed: {traceback.format_exc()}")
            return {
                "success": False,
                "message": str(e)
            }
            
    def create_draft(self, to_address, subject, text_body):
        try:
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0) # 0 is olMailItem
            mail.To = to_address
            mail.Subject = subject
            mail.Body = text_body
            mail.Save() # Saves to drafts
            return True, "Saved to Drafts"
        except Exception as e:
            return False, str(e)

    def send_email(self, to_address, subject, text_body):
        try:
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            mail.To = to_address
            mail.Subject = subject
            mail.Body = text_body
            # Send places it in the Outbox
            mail.Send()
            return True, "Sent to Outbox"
        except Exception as e:
            return False, str(e)
