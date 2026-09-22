import pandas as pd

def process_and_sort_trades(df):
    """
    Sorts the dataframe so that the highest profit-probable trades 
    (% basis) appear on top for each strategy, keeping everything else intact.
    """
    # Assuming your columns are named 'strategy', 'profit_percentage', etc.
    # Replace 'strategy' and 'profit_percentage' with your actual column names if they differ.
    
    # Sort values by strategy and then by profit percentage in descending order
    sorted_df = df.sort_values(
        by=['strategy', 'profit_percentage'], 
        ascending=[True, False]
    )
    
    return sorted_df

# --- Example Usage ---
# data = {
#     'strategy': ['Strat_A', 'Strat_A', 'Strat_B', 'Strat_B'],
#     'trade_id': [1, 2, 3, 4],
#     'profit_percentage': [12.5, 45.2, 8.1, 22.4]
# }
# df = pd.DataFrame(data)
# updated_df = process_and_sort_trades(df)
# print(updated_df)
