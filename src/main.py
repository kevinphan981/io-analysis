import numpy as np
import numpy.typing as npt
import pandas as pd
from pathlib import Path

"""
    Massive overhaul
    ----------------
        - will simply use the published detailed figures from DBEDT instead of calculating them myself. I verified that they worked
          and will trust their calculations 
        - will try to implement more methods for different types of simulations, verified by using known examples
"""
ROOT = Path(__file__).resolve().parent

pd.set_option("display.float_format", lambda x: f"{x:,.2f}")

DATA_PATH = (
    ROOT.parent / "data" / "2022-State-IO-Detailed_Final.xlsx"
) 

# The 'I-O' sheet is laid out with no clean header row for pandas to use automatically,
# so we read it completely raw (header=None) and slice it ourselves by position.
raw = pd.read_excel(DATA_PATH, sheet_name="I-O", header=None)

# we do one conversion so pyright stops crying and the type annotations are correct: forces all empty string cells to be NaN
num: npt.NDArray[np.float64] = np.asarray(
    raw.apply(pd.to_numeric, errors="coerce"), dtype=np.float64
)

N = 62  # number of industries

# --- Industry names ---
industries = raw.iloc[2 : 2 + N, 1].tolist()
print(f"{len(industries)} industries, e.g.:", industries[:3], "...", industries[-2:])

# --- The interindustry transactions matrix Z ---
# Z[i, j] = $ that industry j purchased from industry i
Z = raw.iloc[2 : 2 + N, 2 : 2 + N].apply(pd.to_numeric, errors="coerce").to_numpy()

# --- Total output vector x ---
# Appears twice (row total in col 79, column total in row 75) - they must match.
x_row_total = num[2 : 2 + N, 78]
x_col_total = num[74, 2 : 2 + N]
x = x_row_total  # will have to come back to

# For additional testing
# print("\nTotal output, first 5 industries ($M):", np.round(x[:5], 1))

# --- Final demand block (11 categories) ---
fd_labels = raw.iloc[1, 66:77].tolist()
FD = raw.iloc[2 : 2 + N, 66:77].apply(pd.to_numeric, errors="coerce").to_numpy()
# print("\nFinal demand categories:", fd_labels)

# --- Value-added components (by column, i.e. per producing industry) ---
imports = num[66, 2 : 2 + N]
comp_employees = num[68, 2 : 2 + N]
prop_income = num[69, 2 : 2 + N]
topils = num[70, 2 : 2 + N]
other_capital = num[71, 2 : 2 + N]
value_added = num[72, 2 : 2 + N]

# --- Jobs (by column) ---
wage_salary_jobs = np.asarray(
    pd.to_numeric(raw.iloc[76, 2 : 2 + N], errors="coerce"), dtype=np.float64
)
proprietor_jobs = num[77, 2 : 2 + N]
total_jobs = num[78, 2 : 2 + N]

# --- Earnings specifically prepared by DBEDT for multiplier calculations ---
# (We'll see below this is NOT the same as comp_employees + prop_income -- it's an
#  adjusted BEA RIMS-II earnings concept.)
rims_earnings: npt.NDArray[np.float64] = np.asarray(
    pd.to_numeric(raw.iloc[80, 2 : 2 + N], errors="coerce"), dtype=np.float64
)


# --- Validate against DBEDT's published Type I total requirements matrix ---
#
def sheet_block(sheet: str) -> npt.NDArray[np.float64]:
    df = pd.read_excel(DATA_PATH, sheet_name=sheet, header=None)
    return np.asarray(df.apply(pd.to_numeric, errors="coerce"), dtype=np.float64)[
        2 : 2 + N, 2 : 2 + N
    ]


L1_df = pd.DataFrame(
    sheet_block("ttl req. - type 1"), index=industries, columns=industries
)
L2_df = pd.DataFrame(
    sheet_block("ttl req. - type 2"), index=industries, columns=industries
)

# print("Type I output multiplier range: %.2f to %.2f" % (L1_df.sum(axis=0).min(), L1_df.sum(axis=0).max()))
# print("Type II output multiplier range: %.2f to %.2f" % (L2_df.sum(axis=0).min(), L2_df.sum(axis=0).max()))


# Response Coefficients: Interpreting Final Results

earnings_ratio = rims_earnings / x
ws_jobs_ratio = (
    wage_salary_jobs / x
)  # difference between wage_salary to total is that there is propritetor_jobs (owners)
total_jobs_ratio = total_jobs / x


# Shock Simulator: Bringing the IO model to analyze an event


def simulate_shock(demand_changes: dict, model: str = "type2") -> pd.DataFrame:
    """
    Simulating the economy-wide effect of a change in final demand. Again IO models don't really address supply side changes.

    Parameters
    ----------
    demand_changes: dict[str, float]
          Mapping of industry name with final demand change (in $ millions)
          e.g. {"Accomodation": 50.0, "Eating and drinking": 10.0}
    model: "type1" or "type2"
          type1 -> direct + indirect effects only
          type2 -> direct + indirect + induced effects (household spending).sum() != 0

    Returns
    -------
    pd.DataFrame by industry with cols:
          delta_final_demand, delta_output, delta_earnings,
          delta_ws_jobs, delta_total_jobs

    A final TOTAL row sums each columns
    """
    if model not in ("type1", "type2"):
        raise ValueError("Model must be 'type1' or 'type2'")
    L = L1_df if model == "type1" else L2_df

    df_check = set(demand_changes) - set(industries)
    if df_check:
        raise ValueError(f"Unknown industry names(s): {df_check}")

    delta_f = pd.Series(0.0, index=industries)
    for sector, amount in demand_changes.items():
        delta_f[sector] = amount

    # $ output change by sector
    delta_output = L.to_numpy() @ delta_f.to_numpy(dtype=float)
    delta_x = pd.Series(delta_output, index=industries)

    result = pd.DataFrame(
        {
            "delta_final_demand": delta_f,
            "delta_output": delta_x,
            "delta_earnings": earnings_ratio * delta_output,
            "delta_ws_jobs": ws_jobs_ratio * delta_output,
            "delta_total_jobs": total_jobs_ratio * delta_output,
        }
    )

    result.loc["TOTAL"] = result.sum(numeric_only=True)
    return result


# TODO : must do the other types of simulated shocks (tax, visitor, etc.)


def shock_visitor():
    """
    1. modifies the L1 & L2 to incorporate visitor spending (if it hasn't done so already?)

    """
    return


# is it even worth it since the tax environment changes?
def simulate_tax():
    return


model_1 = simulate_shock({"Accommodation": 50.0})

# minor viewing changes
pd.set_option("display.max_rows", None)  # Show all rows
pd.set_option("display.max_columns", None)  # Show all columns
pd.set_option("display.width", 1000)  # Prevent line-wrapping across multiple lines
pd.set_option(
    "display.max_colwidth", None
)  # Show full content of columns if text is long

print(model_1.head())
print("Simulation Completed")


# output export for easier viewing in markdown
output_dir = ROOT.parent / "examples"
output_file = output_dir / "accommodation_shock_results.md"
model_1.to_markdown(output_file)
