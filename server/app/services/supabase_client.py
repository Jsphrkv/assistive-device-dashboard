from supabase import create_client, Client
from flask import current_app

class SupabaseClient:
    """Singleton Supabase client"""
    _instance = None
    _client: Client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance
    
    def initialize(self, url: str, key: str):
        """Initialize Supabase client"""
        if self._client is None:
            # Simple initialization for supabase 2.27.2
            self._client = create_client(url, key)
    
    @property
    def client(self) -> Client:
        """Get Supabase client instance"""
        if self._client is None:
            self.initialize(
                current_app.config['SUPABASE_URL'],
                current_app.config['SUPABASE_KEY']
            )
        return self._client

# Global instance
supabase_client = SupabaseClient()

def get_supabase() -> Client:
    """Get Supabase client"""
    return supabase_client.client