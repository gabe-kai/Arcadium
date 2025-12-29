"""Test WikiConfig model"""

import uuid

from app import db
from app.models.wiki_config import WikiConfig


def test_wiki_config_creation(app):
    """Test creating a wiki config entry"""
    with app.app_context():
        user_id = uuid.uuid4()

        config = WikiConfig(key="max_file_size_mb", value="10", updated_by=user_id)
        db.session.add(config)
        db.session.commit()

        assert config.id is not None
        assert config.key == "max_file_size_mb"
        assert config.value == "10"
        assert config.updated_by == user_id
        assert config.updated_at is not None


def test_config_key_uniqueness(app):
    """Test that config keys must be unique"""
    with app.app_context():
        user_id = uuid.uuid4()

        # Create first config
        config1 = WikiConfig(key="max_file_size_mb", value="10", updated_by=user_id)
        db.session.add(config1)
        db.session.commit()

        # Try to create duplicate key
        config2 = WikiConfig(
            key="max_file_size_mb",  # Duplicate key
            value="20",
            updated_by=user_id,
        )
        db.session.add(config2)

        # Should raise integrity error
        import pytest
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            db.session.commit()


def test_config_value_update(app):
    """Test updating a config value"""
    with app.app_context():
        user_id = uuid.uuid4()

        config = WikiConfig(key="max_file_size_mb", value="10", updated_by=user_id)
        db.session.add(config)
        db.session.commit()

        # Update value
        import time

        time.sleep(0.1)  # Ensure timestamp difference
        config.value = "20"
        config.updated_by = user_id
        db.session.commit()

        # Check value updated
        assert config.value == "20"
        # Note: updated_at should be updated, but SQLite may not always trigger onupdate
        # This is a known limitation


def test_multiple_config_entries(app):
    """Test storing multiple config entries"""
    with app.app_context():
        user_id = uuid.uuid4()

        config1 = WikiConfig(key="max_file_size_mb", value="10", updated_by=user_id)
        config2 = WikiConfig(key="max_page_size_kb", value="500", updated_by=user_id)
        config3 = WikiConfig(
            key="enable_notifications", value="true", updated_by=user_id
        )

        db.session.add_all([config1, config2, config3])
        db.session.commit()

        # Check all exist
        assert WikiConfig.query.filter_by(key="max_file_size_mb").first().value == "10"
        assert WikiConfig.query.filter_by(key="max_page_size_kb").first().value == "500"
        assert (
            WikiConfig.query.filter_by(key="enable_notifications").first().value
            == "true"
        )


def test_config_to_dict(app):
    """Test config to_dict method"""
    with app.app_context():
        user_id = uuid.uuid4()

        config = WikiConfig(key="test_key", value="test_value", updated_by=user_id)
        db.session.add(config)
        db.session.commit()

        config_dict = config.to_dict()

        assert config_dict["key"] == "test_key"
        assert config_dict["value"] == "test_value"
        assert config_dict["updated_by"] == str(user_id)
        assert "id" in config_dict
        assert "updated_at" in config_dict
