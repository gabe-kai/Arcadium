"""
Migration script to assign test pages (created by CI/CD workflows) to "Regression-Testing" section.

NOTE: This was a one-time migration script to move test pages created by CI/CD workflows
to the "Regression-Testing" section. Regular pages without sections should remain in "No Section".

This script:
1. Finds all pages in the database with section=None or section=""
2. Updates them to section="Regression-Testing"
3. Moves their files to the appropriate directory structure
4. Updates file_path in the database

Run with:
    python scripts/migrate_pages_to_regression_testing.py
"""

import os
import shutil
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.page import Page
from app.services.file_service import FileService
from flask import current_app


def migrate_pages_to_regression_testing():
    """Migrate all pages without sections to Regression-Testing section"""
    app = create_app()

    with app.app_context():
        # Find all pages without sections
        pages_without_section = Page.query.filter(
            (Page.section.is_(None)) | (Page.section == "")
        ).all()

        if not pages_without_section:
            print("No pages found without sections. Migration not needed.")
            return

        print(f"Found {len(pages_without_section)} pages without sections.")
        print("Migrating to 'Regression-Testing' section...")

        pages_dir = current_app.config.get("WIKI_PAGES_DIR", "data/pages")
        migrated_count = 0
        error_count = 0

        for page in pages_without_section:
            try:
                old_file_path = page.file_path
                old_full_path = os.path.join(pages_dir, old_file_path)

                # Update section in database
                page.section = "Regression-Testing"

                # Calculate new file path
                new_file_path = FileService.calculate_file_path(page)
                new_full_path = os.path.join(pages_dir, new_file_path)

                # Update file_path in database
                page.file_path = new_file_path

                # Move file if it exists
                if os.path.exists(old_full_path):
                    # Create directory if it doesn't exist
                    new_dir = os.path.dirname(new_full_path)
                    if new_dir and not os.path.exists(new_dir):
                        os.makedirs(new_dir, exist_ok=True)

                    # Move file
                    if old_full_path != new_full_path:
                        shutil.move(old_full_path, new_full_path)
                        print(f"  Moved: {old_file_path} -> {new_file_path}")
                    else:
                        print(f"  No move needed (same path): {old_file_path}")

                # Update file content to include section in frontmatter
                if os.path.exists(new_full_path):
                    from app.utils.markdown_service import parse_frontmatter

                    with open(new_full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    frontmatter, markdown_content = parse_frontmatter(content)

                    # Update frontmatter
                    frontmatter["section"] = "Regression-Testing"

                    # Rebuild file content
                    import yaml

                    # Build YAML frontmatter
                    frontmatter["title"] = page.title
                    frontmatter["slug"] = page.slug
                    frontmatter["section"] = "Regression-Testing"
                    if page.status:
                        frontmatter["status"] = page.status

                    frontmatter_yaml = yaml.dump(
                        frontmatter, default_flow_style=False, sort_keys=False
                    )
                    file_content = f"---\n{frontmatter_yaml}---\n{markdown_content}"

                    with open(new_full_path, "w", encoding="utf-8") as f:
                        f.write(file_content)

                migrated_count += 1
                print(f"  [OK] Migrated: {page.slug}")

            except Exception as e:
                error_count += 1
                print(f"  [ERROR] Error migrating {page.slug}: {str(e)}")
                continue

        # Commit all changes
        try:
            db.session.commit()
            print(f"\n[SUCCESS] Successfully migrated {migrated_count} pages.")
            if error_count > 0:
                print(f"[WARNING] {error_count} pages had errors.")
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Error committing changes: {str(e)}")
            raise


if __name__ == "__main__":
    migrate_pages_to_regression_testing()
