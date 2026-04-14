import logging
import time
import os

logger = logging.getLogger("ghost_firewall")

class GhostFirewall:
    """
    Automated Defense Layer (Layer 9).
    Translates AI decisions into active infrastructure blocking.
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.block_duration = 86400 # 24 Hours in seconds
        self.enabled = True

    def block_ip(self, ip_address: str, reason: str = "Automated Fraud Detection"):
        """Adds an IP to the active blacklist."""
        if not self.enabled or not self.redis:
            logger.warning(f"Firewall: Mock blocking IP {ip_address} (Reason: {reason})")
            return
        
        try:
            key = f"blocked_ip:{ip_address}"
            # Store block with TTL of 24 hours
            self.redis.setex(key, self.block_duration, reason)
            
            # EXTENSION POINT: 
            # Here you would call an NGINX API, Cloudflare API, or AWS WAF API 
            # e.g., cloudflare_client.block(ip_address)
            
            logger.info(f"🛡️ GHOST FIREWALL: Blacklisted IP {ip_address} for 24h. Reason: {reason}")
        except Exception as e:
            logger.error(f"Firewall Error: {e}")

    def is_blocked(self, ip_address: str) -> bool:
        """Checks if an IP is currently blacklisted."""
        if not self.redis:
            return False
        
        try:
            return self.redis.exists(f"blocked_ip:{ip_address}")
        except:
            return False

# Global instance will be initialized in app.py with the active Redis client.
ghost_firewall = None
