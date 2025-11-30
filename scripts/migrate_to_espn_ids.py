#!/usr/bin/env python3
"""Migrate database to use ESPN numeric IDs as driver primary keys."""

import sys
import logging
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import initialize_database, DEFAULT_DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_database():
    """Backup current database and recreate with new schema."""

    db_path = Path(DEFAULT_DB_PATH)

    if not db_path.exists():
        logger.info("No existing database found, creating new one...")
        initialize_database()
        return

    # Create backup
    backup_path = db_path.parent / f"f1_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    logger.info(f"Backing up database to {backup_path}...")
    shutil.copy2(db_path, backup_path)
    logger.info(f"✓ Backup created: {backup_path}")

    # Delete old database
    logger.info("Removing old database...")
    db_path.unlink()

    # Create new database with updated schema
    logger.info("Creating new database with updated schema...")
    initialize_database()
    logger.info("✓ New database created")

    logger.info("\n" + "="*60)
    logger.info("Migration complete!")
    logger.info(f"Old database backed up to: {backup_path}")
    logger.info("Run populate scripts to repopulate with ESPN numeric IDs")
    logger.info("="*60)


if __name__ == '__main__':
    migrate_database()
