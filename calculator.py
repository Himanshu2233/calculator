"""
calculator.py - Feature-rich CLI Calculator
Supports arithmetic operations, history tracking, and robust error handling.
"""
import sys, io
# Force UTF-8 output so box-drawing / emoji render on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import json
import math
import datetime

# ── ANSI colour helpers ────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
MAGENTA= "\033[95m"
DIM    = "\033[2m"

def c(text, color): return f"{color}{text}{RESET}"

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "calc_history.json")

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
    entry = {
        "expression": expression,
        "result": result,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    history.append(entry)
    save_history(history)

# ── Core Arithmetic ────────────────────────────────────────────────────────────
def add(a, b):        return a + b
def subtract(a, b):   return a - b
def multiply(a, b):   return a * b
def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("Division by zero is undefined.")
    return a / b
def power(a, b):      return a ** b
def modulo(a, b):
    if b == 0:
        raise ZeroDivisionError("Modulo by zero is undefined.")
    return a % b
def floor_div(a, b):
    if b == 0:
        raise ZeroDivisionError("Floor division by zero is undefined.")
    return a // b
def sqrt_op(a):
    if a < 0:
        raise ValueError("Cannot take square root of a negative number.")
    return math.sqrt(a)
def log_op(a, base=10):
    if a <= 0:
        raise ValueError("Logarithm argument must be positive.")
    return math.log(a, base)

OPERATIONS = {
    "+":  (add,       "Addition",       "a + b"),
    "-":  (subtract,  "Subtraction",    "a - b"),
    "*":  (multiply,  "Multiplication", "a * b"),
    "/":  (divide,    "Division",       "a / b"),
    "**": (power,     "Power",          "a ** b"),
    "%":  (modulo,    "Modulo",         "a % b"),
    "//": (floor_div, "Floor Division", "a // b"),
    "sqrt": (sqrt_op, "Square Root",    "sqrt(a)"),
    "log":  (log_op,  "Log base-10",   "log(a)"),
}

UNARY_OPS = {"sqrt", "log"}

# ── Display helpers ────────────────────────────────────────────────────────────
def banner():
    print(c("""
+----------------------------------------------+
|        [=]  CLI Calculator  v1.0  [=]        |
|   Arithmetic  |  History  |  Error Handling  |
+----------------------------------------------+""", CYAN))

def menu():
    print(c("\n-- Operations --", DIM))
    print(f"  {c('+', YELLOW)}     Add            {c('-', YELLOW)}   Subtract")
    print(f"  {c('*', YELLOW)}     Multiply        {c('/', YELLOW)}   Divide")
    print(f"  {c('**', YELLOW)}    Power           {c('%', YELLOW)}   Modulo")
    print(f"  {c('//', YELLOW)}    Floor Div       {c('sqrt', YELLOW)} Square Root")
    print(f"  {c('log', YELLOW)}   Log(base-10)")
    print(c("-- Commands --", DIM))
    print(f"  {c('h', GREEN)}     Show history    {c('c', GREEN)}   Clear history")
    print(f"  {c('m', GREEN)}     Show menu       {c('q', GREEN)}   Quit\n")

def show_history(history):
    if not history:
        print(c("  No history yet.", DIM))
        return
    print(c(f"\n-- Calculation History ({len(history)} entries) --", BLUE))
    for i, entry in enumerate(history, 1):
        print(f"  {c(str(i).rjust(3), DIM)}. {c(entry['expression'], YELLOW)} = "
              f"{c(entry['result'], GREEN)}  {c(entry['timestamp'], DIM)}")
    print()

def format_result(result):
    """Return clean number string: integer if whole, else float."""
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    if isinstance(result, float):
        return f"{result:.10g}"   # up to 10 significant figures, no trailing zeros
    return str(result)

# ── Input helpers ──────────────────────────────────────────────────────────────
def get_number(prompt):
    while True:
        raw = input(c(f"  {prompt}: ", CYAN)).strip()
        if raw == "":
            print(c("  ⚠  Input cannot be empty.", YELLOW))
            continue
        try:
            return float(raw)
        except ValueError:
            print(c(f"  ✗  '{raw}' is not a valid number. Try again.", RED))

def get_operator():
    valid = set(OPERATIONS.keys())
    while True:
        op = input(c("  Operator: ", CYAN)).strip().lower()
        if op in valid:
            return op
        print(c(f"  ✗  Unknown operator '{op}'. Type 'm' to see the menu.", RED))

# ── Main Loop ──────────────────────────────────────────────────────────────────
def main():
    history = load_history()
    banner()
    menu()

    while True:
        print(c("-" * 48, DIM))
        cmd = input(c("  Enter operator (or command): ", MAGENTA)).strip().lower()

        # ── Commands ──
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
                print(c("  ✓  History cleared.", GREEN))
            continue
        elif cmd not in OPERATIONS:
            print(c(f"  ✗  Unknown command '{cmd}'. Type 'm' for menu.", RED))
            continue

        # ── Calculation ──
        func, name, fmt = OPERATIONS[cmd]
        print(c(f"  [{name}]", BLUE))

        try:
            if cmd in UNARY_OPS:
                a = get_number("a")
                result = func(a)
                expr = f"{cmd}({format_result(a)})"
            else:
                a = get_number("a")
                b = get_number("b")
                result = func(a, b)
                expr = f"{format_result(a)} {cmd} {format_result(b)}"

            res_str = format_result(result)
            print(c(f"\n  >>  {expr} = {res_str}\n", GREEN))
            add_to_history(history, expr, res_str)

        except ZeroDivisionError as e:
            print(c(f"\n  ERROR (Math): {e}\n", RED))
        except ValueError as e:
            print(c(f"\n  ERROR (Value): {e}\n", RED))
        except OverflowError:
            print(c("\n  ERROR: Result is too large to display.\n", RED))

if __name__ == "__main__":
    main()
