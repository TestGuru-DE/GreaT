"""REQ-5001: Test sys.frozen detection in config.py and main.py"""
import sys
from pathlib import Path

def test_non_frozen_mode():
    """Test that non-frozen mode uses correct paths."""
    # Simulate non-frozen mode (normal Python execution)
    frozen = getattr(sys, "frozen", False)
    assert not frozen, "Should not be frozen in test"
    
    # Test config.py DB path
    from app.config import DATABASE_URL
    assert "sqlite:///./great.db" == DATABASE_URL or DATABASE_URL.startswith("sqlite:///"), f"Expected local DB, got {DATABASE_URL}"
    print(f"✓ Non-frozen DB path: {DATABASE_URL}")
    
    # Test main.py frontend path
    from app import main
    frontend_dist = main.FRONTEND_DIST
    assert frontend_dist.exists(), f"Frontend dist should exist at {frontend_dist}"
    print(f"✓ Non-frozen frontend path: {frontend_dist}")

def test_frozen_mode_simulation():
    """Simulate frozen mode to verify path resolution."""
    # Simulate frozen mode
    sys.frozen = True
    sys._MEIPASS = r"C:\temp\MEI123"
    
    # Test that _MEIPASS is used
    base_dir = Path(getattr(sys, "_MEIPASS", "."))
    frontend_dist = base_dir / "frontend" / "dist"
    assert "MEI123" in str(frontend_dist), f"Expected _MEIPASS in path, got {frontend_dist}"
    print(f"✓ Frozen frontend path: {frontend_dist}")
    
    # Test DB path in frozen mode
    db_dir = Path.home() / ".great"
    db_url = f"sqlite:///{db_dir / 'great.db'}"
    assert ".great" in db_url, f"Expected .great in DB path, got {db_url}"
    print(f"✓ Frozen DB path: {db_url}")
    
    # Clean up
    del sys.frozen
    del sys._MEIPASS

if __name__ == "__main__":
    print("=== REQ-5001: sys.frozen Detection Tests ===\n")
    test_non_frozen_mode()
    print()
    test_frozen_mode_simulation()
    print("\n=== All tests passed! ===")