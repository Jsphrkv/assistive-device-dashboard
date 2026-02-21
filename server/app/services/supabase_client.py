from supabase import create_client, Client
from flask import current_app

class SupabaseClient:
    """Singleton Supabase client with both user and admin instances"""
    _instance = None
    _user_client: Client = None  # Anon key (respects RLS)
    _admin_client: Client = None  # Service role key (bypasses RLS)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance
    
    def initialize(self, url: str, key: str):
        """Initialize user Supabase client (anon key)"""
        if self._user_client is None:
            self._user_client = create_client(url, key)
            print("✅ User Supabase client initialized (anon key)")
    
    def initialize_admin(self, url: str, service_key: str):
        """Initialize admin Supabase client (service role key)"""
        if self._admin_client is None:
            self._admin_client = create_client(url, service_key)
            print("⚠️  Admin Supabase client initialized (service role key)")
    
    @property
    def client(self) -> Client:
        """Get user Supabase client instance (respects RLS)"""
        if self._user_client is None:
            self.initialize(
                current_app.config['SUPABASE_URL'],
                current_app.config['SUPABASE_KEY']
            )
        return self._user_client
    
    @property
    def admin(self) -> Client:
        """Get admin Supabase client instance (bypasses RLS)"""
        if self._admin_client is None:
            # Try to get service key from config
            service_key = current_app.config.get('SUPABASE_SERVICE_KEY')
            if not service_key:
                raise ValueError(
                    "SUPABASE_SERVICE_KEY not found in config. "
                    "Add it to your .env file and app config."
                )
            self.initialize_admin(
                current_app.config['SUPABASE_URL'],
                service_key
            )
        return self._admin_client

# Global instance
supabase_client = SupabaseClient()

def get_supabase() -> Client:
    """
    Get user Supabase client (respects RLS)
    
    Use this for:
    - User-authenticated operations
    - Operations that should respect Row Level Security
    - Most endpoints with @token_required
    
    Returns:
        Client: Supabase client with anon key
    """
    return supabase_client.client

def get_admin_client() -> Client:
    """
    Get admin Supabase client (bypasses RLS)
    
    ⚠️ WARNING: Use ONLY for:
    - Device operations (@device_token_required)
    - System-level operations
    - Admin operations that need access to all data
    - Operations without user authentication (e.g., pairing)
    
    Returns:
        Client: Supabase client with service role key
    """
    return supabase_client.admin