import ast
import os
import tempfile
from typing import Dict, List, Any

def _is_valid_syntax(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except:
        return False


def _extract_elements(tree: ast.AST) -> List[str]:
    elements = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            elements.append(node.name)
        elif isinstance(node, ast.ClassDef):
            elements.append(node.name)
    return elements


def _check_documentation(tree: ast.AST, code: str) -> float:
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if not functions:
        return 1.0
    
    documented = sum(1 for f in functions if ast.get_docstring(f))
    has_comments = "#" in code
    
    doc_ratio = documented / len(functions) if functions else 0
    return min(1.0, doc_ratio + (0.2 if has_comments else 0))


def _check_style(code: str) -> float:
    score = 1.0
    lines = code.split('\n')
    
    if any(len(line) > 120 for line in lines):
        score -= 0.2
    if '\n\n\n\n' in code:
        score -= 0.1
    if any(word in code.split() for word in ['aa', 'bb', 'xxx', 'tmp123']):
        score -= 0.2
    
    return max(0.0, score)

def _run_test_cases(code: str, test_cases: List[Dict[str, Any]]) -> tuple:
    """Run test cases against the code."""
    passed = 0
    feedback = []
    
    # Create temporary file with student code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Import the module
        import importlib.util
        spec = importlib.util.spec_from_file_location("student_module", temp_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        for i, test in enumerate(test_cases):
            try:
                func_name = test.get("function")
                inputs = test.get("inputs", [])
                expected = test.get("expected")
                
                if not hasattr(module, func_name):
                    feedback.append(f"✗ Test {i+1}: Function '{func_name}' not found")
                    continue
                
                func = getattr(module, func_name)
                result = func(*inputs) if isinstance(inputs, list) else func(**inputs)
                
                if result == expected or (isinstance(expected, float) and abs(result - expected) < 1e-9):
                    passed += 1
                    feedback.append(f"✓ Test {i+1}: Passed")
                else:
                    feedback.append(f"✗ Test {i+1}: Expected {expected}, got {result}")
            except Exception as e:
                feedback.append(f"✗ Test {i+1}: Error - {str(e)[:50]}")
    except Exception as e:
        feedback.append(f"✗ Could not execute code: {str(e)[:100]}")
    finally:
        os.unlink(temp_file)
    
    return passed, len(test_cases), feedback