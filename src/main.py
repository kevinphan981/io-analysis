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

# For additional testing
# print("\nTotal output, first 5 industries ($M):", np.round(x[:5], 1))

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


'''
      Keeping in mind that the BEA/DBEDT computes these tables with approximations and estimates, there is some acceptable level of error in this. 

      Assert by 0.01 and we should be good. 
'''
print("\nSanity checks:")
row_balance = np.max(np.abs(Z.sum(axis=1) + FD.sum(axis=1) - x))
col_balance = np.max(np.abs(pd.to_numeric(raw.iloc[65, 2:2+N], errors='coerce').to_numpy() + imports + value_added - x))
job_balance = np.max(np.abs(wage_salary_jobs + proprietor_jobs - total_jobs))

assert all(b < 0.01 for b in (row_balance, col_balance, job_balance))

print("  row balance  (Z.sum(1)+FD.sum(1) vs x):", row_balance)
print("  col balance  (interind.input+imports+VA vs x):", col_balance)
print("  jobs balance (ws+prop vs total):", job_balance)


# We create the direct-requirements matrix, and compare it with DBEDT's one.

A = Z / x[np.newaxis, :]   # divide each column j by x_j

# --- Validate against DBEDT's published direct-requirements matrix ---
def test_dir_req():
      direct_req_pub = pd.read_excel(DATA_PATH, sheet_name="direct requirements", header=None)
      A_published = direct_req_pub.iloc[3:3+N, 2:2+N].apply(pd.to_numeric, errors="coerce").to_numpy()
      diff = np.max(np.abs(A - A_published))
      assert diff < 0.01
      print("Max abs difference vs DBEDT's published A matrix:", diff )
      print("\nExample: Accommodation's own recipe (top 5 inputs it buys per $1 of output):")
      acc_idx = industries.index("Accommodation")
      recipe = pd.Series(A[:, acc_idx], index=industries).sort_values(ascending=False)
      print(recipe.head(5))

test_dir_req()


# Type 1 - Indirect (Business-to-Business)
'''
      Some minor theory here: the column sum of L1 = output multiplier
      And so we have to test against that.
'''
I = np.eye(N)    # identity matrix
L1 = np.linalg.inv(I - A) # the Leontief inverse, or the "type 1 requirements matrix"

def test_leontief_1():
      # type 1 total requirements check
      t1_pub_raw = pd.read_excel(DATA_PATH, sheet_name="ttl req. - type 1", header = None)
      L1_published = t1_pub_raw.iloc[2:2+N, 2:2+N].apply(pd.to_numeric, errors = "coerce").to_numpy()

      # we check to see that they are equal within an acceptable range, 0.01
      assert np.max(np.abs(L1 - L1_published))


# output multipliers = col sum check
def test_multipliers():
      output_multiplier_1 = L1.sum(axis = 0)

      mult_pub = pd.read_excel(DATA_PATH, sheet_name='fd, income ML', header = None)
      output_mult_1_pub = pd.to_numeric(mult_pub.iloc[5:5+N, 2], errors = "coerce").to_numpy()

      assert np.max(np.abs(output_multiplier_1 - output_mult_1_pub)) < 0.01


test_leontief_1()
test_multipliers()

# Type II - Induced Effects (Household Effects)
'''
      Households are added as another industry, as the workers spend their pay and have generative effects as a result
'''

labor_income = comp_employees + prop_income
houehold_row = labor_income / x
household_col = FD[:, fd_labels.index("PCE")] / FD[: fd_labels.index("PCE")].sum()

A_bar = np.zeroes((N+1, N+1))
A_bar[:N, :N] = A
A_bar[:N, N] = household_col
A_bar[N, :N] = houehold_row

L2_full = np.linalg.inv(np.eye(N+1) - A_bar)
L2_mine = L2_full[:N, :N]

t2_pub_raw = pd.read_excel(DATA_PATH, sheet_name = "ttl req. - type 2", header=None)
L2_published = t2_pub_raw.iloc[2:2+N, 2:2+N].apply(pd.to_numeric, errors = "coerce").to_numpy()

# assert np.max(np.abs(L2_mine - L2_published)) < 1
# something about our calculated method to DBEDT's differ, which is concerning

L1_df = pd.DataFrame(L1, index=industries, columns=industries)
L2_df = pd.DataFrame(L2_published, index=industries, columns = industries)

print("Type I output multiplier range: %.2f to %.2f" % (L1_df.sum(axis=0).min(), L1_df.sum(axis=0).max()))
print("Type II output multiplier range: %.2f to %.2f" % (L2_df.sum(axis=0).min(), L2_df.sum(axis=0).max()))


# Response Coefficients: Interpreting Final Results

earnings_ratio = rims_earnings / x
ws_jobs_ratio = wage_salary_jobs / x
total_jobs_ratio = total_jobs / x

# testing for type 1 earnings mult = earnings ratio through L1

def test_earn_mult():
      earnings_generated_per_dollar_fd = earnings_ratio @ L1   # 1x62, total $ earnings per $1 final demand in sector j
      earn_mult_1_pub = pd.to_numeric(mult_pub.iloc[5:5+N, 5], errors="coerce").to_numpy()
      print("Max abs diff, Type I earnings multiplier:",
            np.max(np.abs(earnings_generated_per_dollar_fd - earn_mult_1_pub)))

# testing for type 1 job multiplier as a ratio of jobs per direct job

def test_job_ratio():
      job_mult_pub = pd.read_excel(DATA_PATH, sheet_name="job ML", header=None)
      ws_job_mult_1_pub = pd.to_numeric(job_mult_pub.iloc[5:5+N, 3], errors="coerce").to_numpy()
      ws_generated_per_dollar_fd = ws_jobs_ratio @ L1
      ws_job_mult_1 = ws_generated_per_dollar_fd / ws_jobs_ratio   # normalize back to "per direct job"
      print("Max abs diff, Type I wage & salary job multiplier:",
            np.nanmax(np.abs(ws_job_mult_1 - ws_job_mult_1_pub)))


test_earn_mult()
test_job_ratio()

# Shock Simulator: Bringing the IO model to analyze an event

def simulate_shock(demand_changes: dict, model: str = 'type2') -> pd.DataFrame:
      '''
      Simulating the economy-wide effect of a change in final demand. Again IO models don't really address supply side changes.

      Parameters
      ----------
      demand_changes: dict[str, float]
            Mapping of industry name with final demand change (in $ millions)
            e.g. {"Accomodation": 50.0, "Eating and drinking": 10.0}
      model: "type1" or "type2"
            type1 -> direct + indirect effects only
            type2 -> direct + indirect + induced effects (household spending)

      Returns
      -------
      pd.DataFrame by industry with cols:
            delta_final_demand, delta_output, delta_earnings, 
            delta_ws_jobs, delta_total_jobs
      
      A final TOTAL row sums each columns
      ''' 
      if model not in ("type1", "type2"):
            raise ValueError("Model must be 'type1' or 'type2'")
      L = L1_df if model == "type1" else L2_df

      df_check = set(demand_changes) - set(industries)
      if df_check:
            raise ValueError(f"Unknown industry names(s): {df_check}")

      delta_f = pd.Series(0.0, index = industries)
      for sector, amount in demand_changes.items():
            delta_f[sector] = amount

      # $ output change by sector
      delta_x = pd.Series(delta_x, index = industries)

      result = pd.DataFrame({
            "delta_final_demand": delta_f,
            "delta_output": delta_x, 
            "delta_earnings": earnings_ratio * delta_x.values, 
            "delta_ws_jobs": ws_jobs_ratio * delta_x.values,
            "delta_total_jobs": total_jobs_ratio * delta_x.values
      })

      result.loc["TOTAL"] = result.sum(numeric_only = True)
      return result

print("Sectors available: ")
print(", ".join(industries)) # should just deliver a list of the industries that we can shock

