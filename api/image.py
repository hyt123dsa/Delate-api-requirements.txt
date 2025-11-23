# server.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
from datetime import datetime
import os
import json
import requests
from email.utils import formatdate

PORT = 8000
LOG_FILE = "access.log"
DISCORD_WEBHOOK = ("\https://discord.com/api/webhooks/1441605740614914079/6TRx4s5dHItAoBQqbqkJ-_a-vAeBgn1L4oJMoH-68bmPmr2W38WgMKwjCGdpRz3tgQ3r")  # Add your Discord webhook URL here
PIXEL_PATH = "/tracking_pixel.gif"
PIXEL_DATA = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

class TrackingHandler(BaseHTTPRequestHandler):
    def log_access(self):
        client_ip = self.client_address[0]
        user_agent = self.headers.get('User-Agent', 'Unknown')
        referer = self.headers.get('Referer', 'Direct')
        timestamp = formatdate(timeval=None, localtime=True, usegmt=True)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'ip': client_ip,
            'user_agent': user_agent,
            'method': self.command,
            'path': self.path,
            'referer': referer
        }
        
        print(f"[{timestamp}] {client_ip} - {user_agent[:50]}...")
        
        with open(LOG_FILE, "a") as log:
            log.write(json.dumps(log_entry) + "\n")
        
        if PIXEL_PATH in self.path and DISCORD_WEBHOOK:
            self.send_discord_alert(client_ip, user_agent, referer)
    
    def send_discord_alert(self, ip, ua, referer):
        embed = {
            "title": "📌 Tracking Pixel Triggered!",
            "color": 5814783,
            "fields": [
                {"name": "Visitor IP", "value": ip, "inline": True},
                {"name": "User Agent", "value": f"```{ua[:1000]}```", "inline": False},
                {"name": "Referer", "value": referer, "inline": True}
            ],
            "footer": {"text": f"Logged at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        }
        
        try:
            requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=5)
        except Exception as e:
            print(f"Discord notification failed: {e}")
    
    def do_GET(self):
        self.log_access()
        
        if self.path == PIXEL_PATH:
            self.send_response(200)
            self.send_header('Content-type', 'image/gif')
            self.send_header('Cache-Control', 'no-store, must-revalidate')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(PIXEL_DATA)
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tracking Server</title>
            <style>
                body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .container {{ background: #f8f9fa; padding: 30px; border-radius: 10px; }}
                .info {{ background: white; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛜 HTTP Tracking Server</h1>
                <div class="info">
                    <p>✅ Server is operational</p>
                    <p>🕒 Time: {datetime.now().strftime('%c')}</p>
                    <p>📍 Your IP: {self.client_address[0]}</p>
                    <p>🖥️ User Agent: {self.headers.get('User-Agent', 'Unknown')[:80]}</p>
                </div>
                <p>This page contains a tracking pixel that logs accesses.</p>
                <img src="{PIXEL_PATH}" alt="tracking pixel">
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))

if __name__ == "__main__":
    print(f"🚀 Starting tracking server on port {PORT}")
    print(f"📝 Access log: {os.path.abspath(LOG_FILE)}")
    print(f"📌 Tracking pixel URL: http://localhost:{PORT}{PIXEL_PATH}")
    print("🛑 Press CTRL+C to stop the server")
    
    with HTTPServer(("", PORT), TrackingHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
