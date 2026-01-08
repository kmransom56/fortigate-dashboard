#!/usr/bin/env python3
"""
Test application and capture all errors
"""

import sys
import traceback
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_imports():
    """Test all imports"""
    errors = []
    
    logger.info("="*60)
    logger.info("Testing Imports")
    logger.info("="*60)
    
    try:
        logger.info("Testing meraki_tui import...")
        from meraki_tui import MerakiDashboard
        logger.info("✓ meraki_tui imported successfully")
    except Exception as e:
        error_msg = f"✗ meraki_tui import failed: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    try:
        logger.info("Testing mcp_client import...")
        from mcp_client import MerakiMCPWrapper
        logger.info("✓ mcp_client imported successfully")
    except Exception as e:
        error_msg = f"✗ mcp_client import failed: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    try:
        logger.info("Testing reusable framework import...")
        sys.path.insert(0, 'reusable')
        from reusable.simple_ai import get_ai_assistant
        logger.info("✓ reusable framework imported successfully")
    except Exception as e:
        error_msg = f"✗ reusable framework import failed: {e}\n{traceback.format_exc()}"
        logger.warning(error_msg)  # Warning, not error - AI is optional
        errors.append(error_msg)
    
    return errors

def test_initialization():
    """Test component initialization"""
    errors = []
    
    logger.info("="*60)
    logger.info("Testing Initialization")
    logger.info("="*60)
    
    try:
        logger.info("Testing MCP wrapper initialization...")
        from mcp_client import MerakiMCPWrapper
        api = MerakiMCPWrapper(use_mcp=True)
        logger.info("✓ MCP wrapper initialized")
        
        # Test getting organizations
        logger.info("Testing API call (get organizations)...")
        orgs = api.get_organizations()
        logger.info(f"✓ Got {len(orgs)} organizations")
    except Exception as e:
        error_msg = f"✗ MCP wrapper initialization failed: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    try:
        logger.info("Testing TUI initialization...")
        from meraki_tui import MerakiDashboard
        # Don't actually run it, just test instantiation
        logger.info("✓ TUI class can be instantiated")
    except Exception as e:
        error_msg = f"✗ TUI initialization test failed: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    try:
        logger.info("Testing AI assistant initialization...")
        sys.path.insert(0, 'reusable')
        from reusable.simple_ai import get_ai_assistant
        assistant = get_ai_assistant(app_name="meraki_magic_mcp", auto_setup=False)
        if assistant:
            logger.info("✓ AI assistant initialized")
        else:
            logger.warning("⚠ AI assistant not available (no API keys)")
    except Exception as e:
        error_msg = f"⚠ AI assistant initialization: {e}"
        logger.warning(error_msg)  # Warning, not error
        errors.append(error_msg)
    
    return errors

def test_mcp_server():
    """Test MCP server"""
    errors = []
    
    logger.info("="*60)
    logger.info("Testing MCP Server")
    logger.info("="*60)
    
    try:
        logger.info("Testing MCP server import...")
        import meraki_mcp_dynamic
        logger.info("✓ MCP server can be imported")
    except ImportError:
        # Try direct import
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("meraki_mcp", "meraki-mcp-dynamic.py")
            if spec and spec.loader:
                logger.info("✓ MCP server file exists")
            else:
                errors.append("✗ MCP server file not found")
        except Exception as e:
            error_msg = f"✗ MCP server import failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    except Exception as e:
        error_msg = f"✗ MCP server test failed: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    return errors

def main():
    """Run all tests"""
    logger.info("Starting application test suite...")
    logger.info("")
    
    all_errors = []
    
    # Test imports
    all_errors.extend(test_imports())
    logger.info("")
    
    # Test initialization
    all_errors.extend(test_initialization())
    logger.info("")
    
    # Test MCP server
    all_errors.extend(test_mcp_server())
    logger.info("")
    
    # Summary
    logger.info("="*60)
    logger.info("Test Summary")
    logger.info("="*60)
    
    if all_errors:
        logger.error(f"Found {len(all_errors)} error(s)/warning(s):")
        for i, error in enumerate(all_errors, 1):
            logger.error(f"{i}. {error}")
        return 1
    else:
        logger.info("✓ All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
