import sys
import pytest

if __name__ == '__main__':
    # Run pytest programmatically and forward exit code
    sys.exit(pytest.main(['-q']))
