import hmac
import hashlib

def verify_webhook_signature(request_body, signature, secret):
    computed = hmac.new(secret.encode(), request_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)
