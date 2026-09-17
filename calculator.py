"""
calculator.py - Feature-rich CLI Calculator
Supports multi-operator expressions, arithmetic operations, history tracking,
and robust error handling.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import ast
import json
import math
import operator
import datetime

# ── ANSI colour helpers ────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
DIM     = "\033[2m"

def c(text, color): return f"{color}{text}{RESET}"

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calc_history.json")

# ── History ────────────────────────────────────────────────────────────────────
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def add_to_history(history, expression, result):
    history.append({
        "expression": expression,
        "result": result,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_history(history)

# ── Safe AST Expression Evaluator ──────────────────────────────────────────────
# Allowed binary operators
_BIN_OPS = {
    ast.Add:      operator.add,
    ast.Sub:      operator.sub,
    ast.Mult:     operator.mul,
    ast.Div:      operator.truediv,
    ast.Pow:      operator.pow,
    ast.Mod:      operator.mod,
    ast.FloorDiv: operator.floordiv,
}

# Allowed unary operators
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Allowed function calls  (name -> callable)
_SAFE_FUNCS = {
    "sqrt": math.sqrt,
    "log":  math.log10,
    "log2": math.log2,
    "ln":   math.log,
    "abs":  abs,
    "ceil": math.ceil,
    "floor": math.floor,
    "sin":  math.sin,
    "cos":  math.cos,
    "tan":  math.tan,
    "round": round,
}

# Allowed constants
_SAFE_NAMES = {
    "pi": math.pi,
    "e":  math.e,
    "tau": math.tau,
    "inf": math.inf,
}

def _eval_node(node):
    """Recursively evaluate an AST node safely."""
    # Numeric literal
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported literal: {node.value!r}")

    # Named constant (pi, e, …)
    if isinstance(node, ast.Name):
        if node.id in _SAFE_NAMES:
            return _SAFE_NAMES[node.id]
        raise NameError(f"Unknown name: '{node.id}'")

    # Binary operation
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BIN_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left  = _eval_node(node.left)
        right = _eval_node(node.right)
        # Guard division-by-zero at eval time
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ZeroDivisionError("Division / modulo by zero.")
        return _BIN_OPS[op_type](left, right)

    # Unary operation  (+x, -x)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return _UNARY_OPS[op_type](_eval_node(node.operand))

    # Function call  sqrt(…), log(…), …
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only named functions are supported.")
        fname = node.func.id
        if fname not in _SAFE_FUNCS:
            raise NameError(f"Unknown function: '{fname}()'")
        args = [_eval_node(a) for a in node.args]
        return _SAFE_FUNCS[fname](*args)

    raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def safe_eval(expr: str) -> float:
    """
    Parse and evaluate a math expression string safely using AST.
    Supports: + - * / ** % //  parentheses  sqrt() log() ln() abs() sin() cos()
              tan() ceil() floor() round()  and constants pi, e, tau
    """
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as e:
        raise SyntaxError(f"Invalid expression syntax: {e.msg}")
    return _eval_node(tree.body)

# ── Format ─────────────────────────────────────────────────────────────────────
def format_result(result):
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    if isinstance(result, float):
        return f"{result:.10g}"
    return str(result)

# ── Display helpers ────────────────────────────────────────────────────────────
def banner():
    print(c("""
+------------------------------------------------+
|      [=]  CLI Calculator  v2.0  [=]            |
|  Multi-Operator  |  History  |  Error Handling |
+------------------------------------------------+""", CYAN))

def menu():
    print(c("\n-- Expression Mode (recommended) --", BOLD + CYAN))
    print(f"  Just type any expression and press Enter:")
    print(c("    3 + 5 * 2 - (10 / 4)", YELLOW))
    print(c("    sqrt(144) + pi * 2 ** 3", YELLOW))
    print(c("    (100 % 7) * log(1000) // 2", YELLOW))

    print(c("\n-- Supported Operators --", DIM))
    print(f"  {c('+  -  *  /', YELLOW)}   Basic arithmetic")
    print(f"  {c('**', YELLOW)}          Power / exponent")
    print(f"  {c('%  //', YELLOW)}        Modulo, floor division")
    print(f"  {c('( )', YELLOW)}          Parentheses / grouping")

    print(c("\n-- Supported Functions --", DIM))
    print(f"  {c('sqrt(x)', YELLOW)}      Square root")
    print(f"  {c('log(x)', YELLOW)}       Log base-10")
    print(f"  {c('ln(x)', YELLOW)}        Natural log")
    print(f"  {c('log2(x)', YELLOW)}      Log base-2")
    print(f"  {c('abs(x)', YELLOW)}       Absolute value")
    print(f"  {c('sin/cos/tan(x)', YELLOW)} Trig (radians)")
    print(f"  {c('ceil/floor(x)', YELLOW)}  Ceiling / floor")
    print(f"  {c('round(x, n)', YELLOW)}  Round to n places")

    print(c("\n-- Constants --", DIM))
    print(f"  {c('pi', YELLOW)}  {c('e', YELLOW)}  {c('tau', YELLOW)}  {c('inf', YELLOW)}")

    print(c("\n-- Commands --", DIM))
    print(f"  {c('h', GREEN)}   Show history    {c('c', GREEN)}   Clear history")
    print(f"  {c('m', GREEN)}   Show menu       {c('q', GREEN)}   Quit\n")


def show_history(history):
    if not history:
        print(c("  No history yet.", DIM))
        return
    print(c(f"\n-- Calculation History ({len(history)} entries) --", BLUE))
    for i, entry in enumerate(history, 1):
        print(f"  {c(str(i).rjust(3), DIM)}. "
              f"{c(entry['expression'], YELLOW)} = "
              f"{c(entry['result'], GREEN)}  "
              f"{c(entry['timestamp'], DIM)}")
    print()

# ── Main Loop ──────────────────────────────────────────────────────────────────
COMMANDS = {"q", "h", "c", "m"}

def main():
    history = load_history()
    banner()
    menu()

    while True:
        print(c("-" * 50, DIM))
        raw = input(c("  >> ", MAGENTA)).strip()

        if not raw:
            continue

        cmd = raw.lower()

        # ── Commands ──────────────────────────────────────────────────────────
        if cmd == "q":
            print(c("\n  Goodbye! All history saved.\n", GREEN))
            break

        elif cmd == "m":
            menu()
            continue

        elif cmd == "h":
            show_history(history)
            continue

        elif cmd == "c":
            confirm = input(c("  Clear all history? (y/n): ", YELLOW)).strip().lower()
            if confirm == "y":
                history.clear()
                save_history(history)
                print(c("  History cleared.", GREEN))
            continue

        # ── Expression Evaluation ─────────────────────────────────────────────
        try:
            result = safe_eval(raw)
            res_str = format_result(result)
            print(c(f"\n  {raw}  =  {res_str}\n", GREEN))
            add_to_history(history, raw, res_str)

        except ZeroDivisionError as e:
            print(c(f"\n  ERROR (Division): {e}\n", RED))
        except (ValueError, TypeError) as e:
            print(c(f"\n  ERROR (Value): {e}\n", RED))
        except NameError as e:
            print(c(f"\n  ERROR (Unknown): {e}  -- type 'm' for help\n", RED))
        except SyntaxError as e:
            print(c(f"\n  ERROR (Syntax): {e}  -- type 'm' for examples\n", RED))
        except OverflowError:
            print(c("\n  ERROR: Result is too large.\n", RED))

if __name__ == "__main__":
    main()
