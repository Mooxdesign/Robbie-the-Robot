#!/usr/bin/env python3

# Test the matching logic
device_name = "USB Audio Device: - (hw:2,0)".lower()
search_name = "USB Audio Device".lower()

print(f"Device: '{device_name}'")
print(f"Search: '{search_name}'")
print(f"Exact match: {device_name == search_name}")
print(f"Starts with '{search_name}:': {device_name.startswith(search_name + ':')}")
print(f"Contains '({search_name})': {f'({search_name})' in device_name}")

# The issue!
print(f"\nActual check in code:")
print(f"  search_name + ':' = '{search_name + ':'}'")
print(f"  Does '{device_name}' start with '{search_name + ':'}'? {device_name.startswith(search_name + ':')}")
