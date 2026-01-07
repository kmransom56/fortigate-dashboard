"""
Unit tests for working_data_functions module
"""
import pytest
from unittest.mock import patch, MagicMock


class TestWorkingDataFunctions:
    """Test cases for working data functions"""

    def test_get_working_brands_data(self):
        """Test get_working_brands_data function"""
        from src.working_data_functions import get_working_brands_data

        result = get_working_brands_data()

        # Check response structure
        assert result["success"] is True
        assert "brands" in result
        assert "total_brands" in result
        assert "total_devices" in result

        # Check brands data
        brands = result["brands"]
        assert len(brands) == 3

        # Check specific brands
        brand_codes = [brand["code"] for brand in brands]
        assert "BWW" in brand_codes
        assert "ARBYS" in brand_codes
        assert "SONIC" in brand_codes

        # Check brand structure
        bww_brand = next(brand for brand in brands if brand["code"] == "BWW")
        assert bww_brand["name"] == "Buffalo Wild Wings"
        assert "device_count" in bww_brand
        assert "status" in bww_brand
        assert "fortimanager" in bww_brand

    def test_get_working_bww_overview(self):
        """Test get_working_bww_overview function"""
        from src.working_data_functions import get_working_bww_overview

        result = get_working_bww_overview()

        # Check response structure
        assert result["success"] is True
        assert result["brand"] == "BWW"
        assert "overview" in result

        # Check overview data
        overview = result["overview"]
        assert "total_stores" in overview
        assert "online_stores" in overview
        assert "offline_stores" in overview
        assert "last_updated" in overview

        # Check data consistency
        assert overview["total_stores"] == overview["online_stores"] + overview["offline_stores"]

    def test_get_working_store_security(self):
        """Test get_working_store_security function"""
        from src.working_data_functions import get_working_store_security

        result = get_working_store_security("BWW", "00123")

        # Check response structure
        assert result["success"] is True
        assert result["brand"] == "BWW"
        assert result["store_id"] == "00123"
        assert "security_status" in result

        # Check security status
        security_status = result["security_status"]
        assert "overall" in security_status
        assert "firewall" in security_status
        assert "last_policy_update" in security_status
        assert "threat_level" in security_status
        assert "recent_events" in security_status

        # Check valid values
        assert security_status["overall"] in ["GOOD", "WARNING", "CRITICAL"]
        assert security_status["firewall"] in ["ACTIVE", "INACTIVE", "ERROR"]
        assert security_status["threat_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    @pytest.mark.parametrize("brand,store_id", [
        ("BWW", "00123"),
        ("ARBYS", "00456"),
        ("SONIC", "00789"),
        ("UNKNOWN", "00000"),
    ])
    def test_get_working_store_security_different_brands(self, brand, store_id):
        """Test get_working_store_security with different brands"""
        from src.working_data_functions import get_working_store_security

        result = get_working_store_security(brand, store_id)

        assert result["success"] is True
        assert result["brand"] == brand
        assert result["store_id"] == store_id
        assert "security_status" in result

    def test_functions_return_consistent_data(self):
        """Test that functions return consistent data across calls"""
        from src.working_data_functions import (
            get_working_brands_data,
            get_working_bww_overview,
            get_working_store_security
        )

        # Get brands data
        brands_data = get_working_brands_data()
        bww_brand = next(brand for brand in brands_data["brands"] if brand["code"] == "BWW")

        # Get BWW overview
        overview_data = get_working_bww_overview()

        # Check consistency
        assert bww_brand["device_count"] == overview_data["overview"]["total_stores"]

    def test_error_handling_invalid_inputs(self):
        """Test error handling for invalid inputs"""
        from src.working_data_functions import get_working_store_security

        # Test with empty brand
        result = get_working_store_security("", "00123")
        assert result["success"] is True  # Function should handle gracefully

        # Test with empty store_id
        result = get_working_store_security("BWW", "")
        assert result["success"] is True  # Function should handle gracefully

        # Test with None values
        result = get_working_store_security(None, None)
        assert result["success"] is True  # Function should handle gracefully
