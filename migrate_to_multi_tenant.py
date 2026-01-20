"""
Database migration script to add multi-tenant support.
Adds tenant_id columns to existing tables and creates tenant/user tables.
"""
import sys
import logging
from sqlalchemy import text
from database import db, Base, TenantDB, UserDB, CapabilityProfileDB, OpportunityScoreDB
from config import settings

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """Migrate database to support multi-tenancy."""
    session = db.get_session()
    
    try:
        # Create new tables (Tenant, User) if they don't exist
        logger.info("Creating tenant and user tables...")
        Base.metadata.create_all(bind=db.engine, tables=[TenantDB.__table__, UserDB.__table__])
        
        # Check if tenant_id column exists in capability_profiles
        logger.info("Checking capability_profiles table...")
        result = session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='capability_profiles'
        """))
        
        if result.fetchone():
            # Check if tenant_id column exists
            result = session.execute(text("PRAGMA table_info(capability_profiles)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'tenant_id' not in columns:
                logger.info("Adding tenant_id column to capability_profiles...")
                session.execute(text("ALTER TABLE capability_profiles ADD COLUMN tenant_id INTEGER"))
                # Create default tenant for existing profiles
                default_tenant = TenantDB(name="Default Organization", domain="default")
                session.add(default_tenant)
                session.commit()
                session.refresh(default_tenant)
                
                # Update existing profiles to use default tenant
                session.execute(text("""
                    UPDATE capability_profiles 
                    SET tenant_id = :tenant_id 
                    WHERE tenant_id IS NULL
                """), {"tenant_id": default_tenant.id})
                logger.info(f"Migrated existing profiles to default tenant (ID: {default_tenant.id})")
            else:
                logger.info("tenant_id column already exists in capability_profiles")
        
        # Check if tenant_id column exists in opportunity_scores
        logger.info("Checking opportunity_scores table...")
        result = session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='opportunity_scores'
        """))
        
        if result.fetchone():
            result = session.execute(text("PRAGMA table_info(opportunity_scores)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'tenant_id' not in columns:
                logger.info("Adding tenant_id column to opportunity_scores...")
                session.execute(text("ALTER TABLE opportunity_scores ADD COLUMN tenant_id INTEGER"))
                logger.info("Added tenant_id column to opportunity_scores")
            else:
                logger.info("tenant_id column already exists in opportunity_scores")
        
        # Add unique constraint for tenant_id + company_name if it doesn't exist
        # Note: SQLite doesn't support adding constraints easily, so we'll skip this
        # The constraint will be enforced at the application level
        
        session.commit()
        logger.info("✅ Database migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Adding Multi-Tenant Support")
    print("=" * 60)
    print()
    print("This will:")
    print("  1. Create tenant and user tables")
    print("  2. Add tenant_id to capability_profiles")
    print("  3. Add tenant_id to opportunity_scores")
    print("  4. Create a default tenant for existing data")
    print()
    print("Running migration...")
    
    try:
        migrate_database()
        print()
        print("✅ Migration complete! You can now use the app with multi-tenant support.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
