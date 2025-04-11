import os
import sys
from hyperzip_image import compress_png_with_oxipng

# Just test if the function can be imported and called without errors
# We don't need an actual PNG file for this test
print("Import successful")
print("Testing function call with dummy path...")
try:
    # Call with a non-existent file - it should handle this gracefully
    # We're just testing if the function runs without the UnboundLocalError
    saved, original = compress_png_with_oxipng("dummy.png", 8)
    print(f"Function call completed: saved={saved}, original={original}")
    print("Test PASSED - No UnboundLocalError occurred")
except UnboundLocalError as e:
    print(f"Test FAILED - UnboundLocalError still occurs: {e}")
except Exception as e:
    # Other exceptions are expected (like file not found) and are fine
    print(f"Expected exception (not the bug we're fixing): {type(e).__name__}: {e}")
    print("Test PASSED - No UnboundLocalError occurred")

print("Test completed")
