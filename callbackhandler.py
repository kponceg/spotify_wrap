import urllib.parse

#minimal local callback server
auth_code_holder = {"code": None, "error": None}

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        qs = urllib.parse.parse_qs(parsed.query)
        if "error" in qs:
            auth_code_holder["error"] = qs["error"][0]
        if "code" in qs:
            auth_code_holder["code"] = qs["code"][0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"<h2>Logged in! Close tab and return to terminal.</h2>")

    def log_message(self, format, *args):
        #silence server calls
        return

