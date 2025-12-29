#!/usr/bin/env python
"""
Cleanup script to remove pages from database that have missing files.

This script finds all pages in the database whose corresponding files don't exist
on disk and optionally deletes them.

Usage:
    # Dry run (show what would be deleted)
    python scripts/cleanup_missing_files.py --dry-run

    # Actually delete the pages
    python scripts/cleanup_missing_files.py --delete

    # Delete specific pages by slug
    python scripts/cleanup_missing_files.py --delete --slugs test-page test-slug
"""

import argparse
import os
import sys

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.page import Page
from app.services.file_service import FileService


def find_pages_with_missing_files():
    """Find all pages whose files don't exist on disk"""
    pages_with_missing_files = []

    all_pages = Page.query.all()
    for page in all_pages:
        full_path = FileService.get_full_path(page.file_path)
        if not os.path.exists(full_path):
            pages_with_missing_files.append(page)

    return pages_with_missing_files


def delete_page(page: Page, dry_run: bool = False):
    """Delete a page (or simulate deletion if dry_run)"""
    print(
        f"{'[DRY RUN] Would delete' if dry_run else 'Deleting'}: {page.title} (slug: {page.slug}, id: {page.id})"
    )

    if not dry_run:
        # Check if page has children
        children = Page.query.filter_by(parent_id=page.id).all()
        if children:
            print(
                f"  Warning: Page has {len(children)} child pages. They will be orphaned."
            )

        page_id = page.id

        # Delete index entries first (required before page deletion)
        from app.models.index_entry import IndexEntry

        index_count = IndexEntry.query.filter_by(page_id=page_id).count()
        if index_count > 0:
            IndexEntry.query.filter_by(page_id=page_id).delete()
            print(f"  Deleted {index_count} index entries")

        # Delete comments
        from app.models.comment import Comment

        comment_count = Comment.query.filter_by(page_id=page_id).count()
        if comment_count > 0:
            Comment.query.filter_by(page_id=page_id).delete()
            print(f"  Deleted {comment_count} comments")

        # Delete related versions
        from app.models.page_version import PageVersion

        version_count = PageVersion.query.filter_by(page_id=page_id).count()
        if version_count > 0:
            PageVersion.query.filter_by(page_id=page_id).delete()
            print(f"  Deleted {version_count} versions")

        # Clean up links
        from app.services.link_service import LinkService

        LinkService.handle_page_deletion(page_id)

        # Delete file (if it exists - might already be deleted)
        try:
            from app.services.file_service import FileService

            FileService.delete_page_file(page)
        except Exception:
            pass  # File might already be deleted

        # Delete the page
        db.session.delete(page)
        db.session.commit()
        print("  ✓ Deleted successfully")


def main():
    parser = argparse.ArgumentParser(description="Cleanup pages with missing files")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete the pages (use with caution!)",
    )
    parser.add_argument(
        "--slugs",
        nargs="+",
        help="Only process specific page slugs",
    )

    args = parser.parse_args()

    if not args.dry_run and not args.delete:
        print("Error: Must specify either --dry-run or --delete")
        parser.print_help()
        sys.exit(1)

    if args.dry_run and args.delete:
        print("Error: Cannot use both --dry-run and --delete")
        parser.print_help()
        sys.exit(1)

    app = create_app()
    with app.app_context():
        if args.slugs:
            # Process specific slugs
            pages_to_process = []
            for slug in args.slugs:
                page = Page.query.filter_by(slug=slug).first()
                if page:
                    full_path = FileService.get_full_path(page.file_path)
                    if not os.path.exists(full_path):
                        pages_to_process.append(page)
                    else:
                        print(f"Warning: {slug} file exists, skipping")
                else:
                    print(f"Warning: Page with slug '{slug}' not found")
        else:
            # Find all pages with missing files
            pages_to_process = find_pages_with_missing_files()

        if not pages_to_process:
            print("No pages with missing files found.")
            return

        print(f"\nFound {len(pages_to_process)} page(s) with missing files:\n")

        for page in pages_to_process:
            delete_page(page, dry_run=args.dry_run)

        if args.dry_run:
            print(f"\n[DRY RUN] Would delete {len(pages_to_process)} page(s).")
            print("Run with --delete to actually delete them.")
        else:
            print(f"\n✓ Deleted {len(pages_to_process)} page(s).")


if __name__ == "__main__":
    main()
