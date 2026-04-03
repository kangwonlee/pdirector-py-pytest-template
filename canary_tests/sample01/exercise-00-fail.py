# Canary sample: fails test_style (module-level executable code)
# test_function_only_in_py_file requires all code to be inside functions.
# This sample has bare statements at module level.

result = 2 + 3
print(result)
