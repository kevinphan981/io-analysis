import numpy as np
import pandas as pd
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent 

print(os.getcwd())
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")

DATA_PATH = ROOT.parent / "data" / "2022-State-IO-Detailed_Final.xlsx"  # <- put the file next to this notebook

# The 'I-O' sheet is laid out with no clean header row for pandas to use automatically,
# so we read it completely raw (header=None) and slice it ourselves by position.
raw = pd.read_excel(DATA_PATH, sheet_name="I-O", header=None)

N = 62  # number of industries

# --- Industry names ---
industries = raw.iloc[2:2+N, 1].tolist()
print(f"{len(industries)} industries, e.g.:", industries[:3], "...", industries[-2:])

# --- The interindustry transactions matrix Z ---
# Z[i, j] = $ that industry j purchased from industry i
Z = raw.iloc[2:2+N, 2:2+N].apply(pd.to_numeric, errors="coerce").to_numpy()

# --- Total output vector x ---
# Appears twice (row total in col 79, column total in row 75) - they must match.
x_row_total = pd.to_numeric(raw.iloc[2:2+N, 78], errors="coerce").to_numpy()
x_col_total = pd.to_numeric(raw.iloc[74, 2:2+N], errors="coerce").to_numpy()
assert np.allclose(x_row_total, x_col_total), "Row/column output totals should match!"
x = x_row_total
print("\nTotal output, first 5 industries ($M):", np.round(x[:5], 1))

# --- Final demand block (11 categories) ---
fd_labels = raw.iloc[1, 66:77].tolist()
FD = raw.iloc[2:2+N, 66:77].apply(pd.to_numeric, errors="coerce").to_numpy()
print("\nFinal demand categories:", fd_labels)

# --- Value-added components (by column, i.e. per producing industry) ---
imports        = pd.to_numeric(raw.iloc[66, 2:2+N], errors="coerce").to_numpy()
comp_employees = pd.to_numeric(raw.iloc[68, 2:2+N], errors="coerce").to_numpy()
prop_income    = pd.to_numeric(raw.iloc[69, 2:2+N], errors="coerce").to_numpy()
topils         = pd.to_numeric(raw.iloc[70, 2:2+N], errors="coerce").to_numpy()
other_capital  = pd.to_numeric(raw.iloc[71, 2:2+N], errors="coerce").to_numpy()
value_added    = pd.to_numeric(raw.iloc[72, 2:2+N], errors="coerce").to_numpy()

# --- Jobs (by column) ---
wage_salary_jobs = pd.to_numeric(raw.iloc[76, 2:2+N], errors="coerce").to_numpy()
proprietor_jobs  = pd.to_numeric(raw.iloc[77, 2:2+N], errors="coerce").to_numpy()
total_jobs       = pd.to_numeric(raw.iloc[78, 2:2+N], errors="coerce").to_numpy()

# --- Earnings specifically prepared by DBEDT for multiplier calculations ---
# (We'll see below this is NOT the same as comp_employees + prop_income -- it's an
#  adjusted BEA RIMS-II earnings concept.)
rims_earnings = pd.to_numeric(raw.iloc[80, 2:2+N], errors="coerce").to_numpy()

print("\nSanity checks:")
print("  row balance  (Z.sum(1)+FD.sum(1) vs x):",
      np.max(np.abs(Z.sum(axis=1) + FD.sum(axis=1) - x)))
print("  col balance  (interind.input+imports+VA vs x):",
      np.max(np.abs(pd.to_numeric(raw.iloc[65, 2:2+N], errors='coerce').to_numpy()
                    + imports + value_added - x)))
print("  jobs balance (ws+prop vs total):",
      np.max(np.abs(wage_salary_jobs + proprietor_jobs - total_jobs)))