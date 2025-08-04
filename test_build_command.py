#!/usr/bin/env python
"""Test the enhanced build_command_string method"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from django_jobs.models import CommandSchedule

# Test cases
test_cases = [
    # Test 1: Only keyword arguments (backward compatibility)
    {
        "name": "Keyword args only",
        "command": "fetch_latest_candles",
        "args": {
            "symbol": "BTC/USDT",
            "timeframe": "1m",
            "calculate_indicators": True
        }
    },
    
    # Test 2: Only positional arguments
    {
        "name": "Positional args only",
        "command": "fetch_latest_candles",
        "args": {
            "_positional": ["BTC/USDT", "1m"]
        }
    },
    
    # Test 3: Mixed positional and keyword arguments
    {
        "name": "Mixed args",
        "command": "fetch_latest_candles",
        "args": {
            "_positional": ["BTC/USDT", "1m"],
            "calculate_indicators": True,
            "dry_run": True
        }
    },
    
    # Test 4: Single positional argument (not a list)
    {
        "name": "Single positional arg",
        "command": "some_command",
        "args": {
            "_args": "single_value"
        }
    },
    
    # Test 5: Arguments with special characters
    {
        "name": "Special characters",
        "command": "test_command",
        "args": {
            "_positional": ["path/with spaces/file.txt", "value with 'quotes'"],
            "message": "Hello \"World\""
        }
    }
]

# Run tests
for test in test_cases:
    print(f"\n{test['name']}:")
    print(f"Input: {test['args']}")
    result = CommandSchedule.build_command_string(test['command'], test['args'])
    print(f"Output: {result}")