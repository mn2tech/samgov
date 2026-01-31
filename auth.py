"""
Google OAuth Authentication for Streamlit Multi-Tenant App.
Handles user authentication via Google Sign-In and tenant management.
"""
import streamlit as st
import logging
from typing import Optional, Dict
from datetime import datetime
import json

try:
    from google.oauth2 import id_token
    from google.auth.transport import requests
    from google_auth_oauthlib.flow import Flow
    import google.auth.exceptions
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    logging.warning("Google auth libraries not installed. Install with: pip install google-auth google-auth-oauthlib")

from config import settings
from database import db

logger = logging.getLogger(__name__)


class GoogleAuth:
    """Google OAuth authentication handler."""
    
    def __init__(self):
        self.client_id = getattr(settings, 'google_client_id', None)
        self.client_secret = getattr(settings, 'google_client_secret', None)
        self.redirect_uri = getattr(settings, 'google_redirect_uri', None)
        
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify Google ID token and return user info.
        
        Args:
            token: Google ID token from OAuth flow
            
        Returns:
            User info dict with email, name, etc. or None if invalid
        """
        if not GOOGLE_AUTH_AVAILABLE:
            logger.error("Google auth libraries not available")
            return None
            
        if not self.client_id:
            logger.warning("Google Client ID not configured")
            return None
        
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.client_id
            )
            
            # Verify issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return {
                'email': idinfo.get('email'),
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'sub': idinfo.get('sub'),  # Google user ID
                'email_verified': idinfo.get('email_verified', False)
            }
        except ValueError as e:
            logger.error(f"Token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def get_login_url(self) -> str:
        """Generate Google OAuth login URL."""
        if not self.client_id:
            return None
        
        # Use redirect URI from config, ensure it's properly formatted
        redirect_uri = self.redirect_uri or "http://localhost:8501"
        # Remove trailing slash if present (Google is strict about exact match)
        redirect_uri = redirect_uri.rstrip('/')
        
        # URL encode the redirect URI
        from urllib.parse import quote
        redirect_uri_encoded = quote(redirect_uri, safe='')
        
        scopes = "openid email profile"
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={self.client_id}&"
            f"redirect_uri={redirect_uri_encoded}&"
            f"response_type=code&"
            f"scope={scopes}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        return auth_url
    
    def exchange_code_for_user_info(self, code: str) -> Optional[Dict]:
        """
        Exchange OAuth authorization code for user info.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            User info dict or None if failed
        """
        if not GOOGLE_AUTH_AVAILABLE:
            logger.error("Google auth libraries not available")
            return None
            
        if not self.client_id or not self.client_secret:
            logger.warning("Google OAuth credentials not configured")
            return None
        
        try:
            # Prepare redirect URI
            redirect_uri = self.redirect_uri or "http://localhost:8501"
            redirect_uri = redirect_uri.rstrip('/')
            
            # Exchange code for token
            import requests as http_requests
            
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = http_requests.post(token_url, data=token_data)
            response.raise_for_status()
            
            token_response = response.json()
            id_token_str = token_response.get('id_token')
            
            if not id_token_str:
                logger.error("No ID token in response")
                return None
            
            # Verify and decode ID token
            return self.verify_token(id_token_str)
            
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None


def check_authentication() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get('authenticated', False)


def get_current_user() -> Optional[Dict]:
    """Get current authenticated user info."""
    if check_authentication():
        return st.session_state.get('user', None)
    return None


def get_current_tenant_id() -> Optional[int]:
    """Get current user's tenant ID."""
    user = get_current_user()
    if user:
        return user.get('tenant_id')
    return None


def require_auth(func):
    """Decorator to require authentication for a function."""
    def wrapper(*args, **kwargs):
        if not check_authentication():
            show_login_page()
            return
        return func(*args, **kwargs)
    return wrapper


def show_login_page():
    """Display Google OAuth login page."""
    st.title("🔐 Login to AI Contract Finder")
    st.markdown("Sign in with your Google account to access the platform.")
    
    auth = GoogleAuth()
    
    # Show warning if Google OAuth not configured, but still allow demo mode
    if not auth.client_id:
        st.warning("⚠️ Google OAuth not configured. Demo mode is available below.")
        with st.expander("📖 How to set up Google OAuth (optional)"):
            st.info("""
            **To set up Google OAuth:**
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Create a new project or select existing
            3. Enable Google+ API or People API
            4. Create OAuth 2.0 credentials
            5. Add authorized redirect URI: `http://localhost:8501` (or your Streamlit Cloud URL)
            6. Add to `.env` or Streamlit Cloud secrets:
               ```
               GOOGLE_CLIENT_ID=your_client_id
               GOOGLE_CLIENT_SECRET=your_client_secret
               GOOGLE_REDIRECT_URI=http://localhost:8501
               ```
            
            **For Streamlit Cloud:**
            - Add these as environment variables in your app settings
            - Use your Streamlit Cloud URL as the redirect URI (e.g., `https://your-app.streamlit.app`)
            - Add the same URL to authorized redirect URIs in Google Console
            """)
        st.markdown("---")
    
    # Check for OAuth callback
    # Handle both old and new Streamlit versions
    try:
        # Try new Streamlit API (1.28.0+)
        if hasattr(st, 'query_params'):
            query_params = st.query_params
            code = query_params.get('code', [None])[0] if isinstance(query_params.get('code'), list) else query_params.get('code')
        else:
            # Fallback to old API
            query_params = st.experimental_get_query_params()
            code = query_params.get('code', [None])[0]
    except Exception as e:
        logger.warning(f"Error getting query params: {e}")
        code = None
    
    if code:
        
        with st.spinner("Authenticating with Google..."):
            try:
                # Exchange authorization code for tokens
                user_info = auth.exchange_code_for_user_info(code)
                
                if user_info:
                    # Get or create tenant based on email domain
                    tenant = db.get_or_create_tenant_by_email(user_info['email'])
                    
                    # Get or create user
                    user = db.get_or_create_user(user_info, tenant.id)
                    
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.user = {
                        'id': user.id,
                        'email': user.email,
                        'name': user.name,
                        'tenant_id': tenant.id,
                        'tenant_name': tenant.name
                    }
                    
                    # Security: Clear OAuth callback code from URL to prevent accidental sharing
                    # The authorization code has been exchanged for tokens and stored in session state
                    # We must remove it from the URL immediately after use
                    try:
                        # Try new Streamlit API (1.28.0+) - clear all query params
                        if hasattr(st, 'query_params'):
                            st.query_params.clear()
                        # Fallback to experimental API - set empty dict to clear all params
                        elif hasattr(st, 'experimental_set_query_params'):
                            st.experimental_set_query_params()
                    except Exception as e:
                        logger.warning(f"Could not clear query params: {e}")
                    
                    st.success(f"✅ Successfully logged in as {user_info['email']}")
                    # Force rerun to refresh page with clean URL (no ?code=...)
                    st.rerun()
                else:
                    st.error("❌ Authentication failed. Please try again.")
                    
            except Exception as e:
                logger.error(f"OAuth callback error: {e}")
                st.error(f"❌ Authentication error: {str(e)}")
                st.info("💡 You can use Demo Mode below to continue testing.")
        return
    
    # Show login button (only if Google OAuth is configured)
    if auth.client_id:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Sign in with Google")
            
            # Generate login URL
            login_url = auth.get_login_url()
            
            if login_url:
                # Detect if we're on Streamlit Cloud
                # On Streamlit Cloud, OAuth redirects work better in a new tab
                # due to iframe restrictions and security policies
                is_streamlit_cloud = False
                if auth.redirect_uri:
                    # Check redirect URI for Streamlit Cloud patterns
                    is_streamlit_cloud = (
                        'streamlit.app' in auth.redirect_uri or 
                        'share.streamlit.io' in auth.redirect_uri or
                        auth.redirect_uri.startswith('https://') and 'localhost' not in auth.redirect_uri
                    )
                
                # Use _blank for Streamlit Cloud, _self for local
                # This ensures OAuth redirects work properly on Streamlit Cloud
                target = "_blank" if is_streamlit_cloud else "_self"
                
                # Add a helpful note for Streamlit Cloud users
                if is_streamlit_cloud:
                    st.info("💡 **Note:** Sign-in will open in a new tab. After signing in with Google, you'll be redirected back to the app automatically.")
                
                # Use Streamlit link button instead of external image to avoid ERR_BLOCKED_BY_CLIENT
                # (browser extensions often block external images from Google CDN)
                # Create a clickable link styled as a button
                st.markdown(f"""
                <a href="{login_url}" target="{target}" rel="noopener noreferrer" style="text-decoration: none;">
                    <div style="background-color: #4285F4; color: white; padding: 12px 24px; border-radius: 4px; text-align: center; font-weight: bold; cursor: pointer;">
                        🔐 Sign in with Google
                    </div>
                </a>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("**Or use demo mode:**")
    else:
        st.markdown("### Demo Mode Login")
        st.info("💡 Enter your email below to access the app in demo mode.")
    
    # Demo mode (always available)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        
        demo_email = st.text_input("Email (for demo)", placeholder="user@example.com")
        if st.button("Login (Demo)", type="primary"):
            if demo_email:
                # Create or get user/tenant
                user_info = {
                    'email': demo_email,
                    'name': demo_email.split('@')[0],
                    'sub': demo_email,  # Use email as ID for demo
                    'email_verified': True
                }
                
                # Get or create tenant
                tenant = db.get_or_create_tenant_by_email(demo_email)
                user = db.get_or_create_user(user_info, tenant.id)
                
                # Set session
                st.session_state.authenticated = True
                st.session_state.user = {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'tenant_id': tenant.id,
                    'tenant_name': tenant.name
                }
                st.rerun()


def logout():
    """Logout current user."""
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    if 'user' in st.session_state:
        del st.session_state.user
    if 'profile' in st.session_state:
        st.session_state.profile = None
    if 'scores' in st.session_state:
        st.session_state.scores = []
    if 'opportunities' in st.session_state:
        st.session_state.opportunities = []
    st.rerun()

