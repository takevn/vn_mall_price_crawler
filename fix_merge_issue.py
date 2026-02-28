"""
Fix script for KeyError: 'Model' in pandas merge operation
This script provides functions to fix the merge issue at line 366
"""

import pandas as pd
import sys

def ensure_model_column(df, model_column_name='Model', fallback_index=False):
    """
    Ensure DataFrame has a 'Model' column before merging.
    
    Args:
        df: DataFrame to check/fix
        model_column_name: Name of the model column (default: 'Model')
        fallback_index: If True, use index as Model if column doesn't exist
    
    Returns:
        DataFrame with 'Model' column guaranteed
    """
    if model_column_name not in df.columns:
        print(f"Warning: '{model_column_name}' column not found in DataFrame")
        print(f"Available columns: {df.columns.tolist()}")
        
        if fallback_index:
            # Use index as Model
            df = df.reset_index()
            if 'index' in df.columns:
                df[model_column_name] = df['index']
                df = df.drop('index', axis=1)
            else:
                df[model_column_name] = range(len(df))
            print(f"Created '{model_column_name}' column from index")
        else:
            # Try to find similar column names
            possible_names = [col for col in df.columns if 'model' in col.lower() or 'name' in col.lower()]
            if possible_names:
                df[model_column_name] = df[possible_names[0]]
                print(f"Created '{model_column_name}' column from '{possible_names[0]}'")
            else:
                # Create Model column with sequential numbers
                df[model_column_name] = [f"Item_{i+1}" for i in range(len(df))]
                print(f"Created '{model_column_name}' column with sequential names")
    
    return df


def safe_merge(left_df, right_df, on='Model', how='left', **kwargs):
    """
    Safe merge function that ensures both DataFrames have the merge key.
    
    Args:
        left_df: Left DataFrame
        right_df: Right DataFrame  
        on: Column name(s) to merge on
        how: Type of merge ('left', 'right', 'inner', 'outer')
        **kwargs: Additional arguments for pd.merge
    
    Returns:
        Merged DataFrame
    """
    # Ensure both DataFrames have the merge key
    if isinstance(on, str):
        on_list = [on]
    else:
        on_list = on
    
    for key in on_list:
        if key not in left_df.columns:
            print(f"Error: '{key}' not in left DataFrame columns: {left_df.columns.tolist()}")
            left_df = ensure_model_column(left_df, key, fallback_index=True)
        
        if key not in right_df.columns:
            print(f"Error: '{key}' not in right DataFrame columns: {right_df.columns.tolist()}")
            right_df = ensure_model_column(right_df, key, fallback_index=True)
    
    # Perform merge
    try:
        result = pd.merge(left_df, right_df, on=on, how=how, **kwargs)
        print(f"Merge successful: {len(result)} rows")
        return result
    except Exception as e:
        print(f"Merge failed: {e}")
        raise


# Example usage pattern for line 366 fix:
"""
# BEFORE (line 366 - original code that causes error):
result = pd.merge(original_df, scraped_df, on='Model', how='left')

# AFTER (fixed code):
from fix_merge_issue import safe_merge
result = safe_merge(original_df, scraped_df, on='Model', how='left')

# OR if you want to fix the DataFrames first:
from fix_merge_issue import ensure_model_column
scraped_df = ensure_model_column(scraped_df, 'Model', fallback_index=True)
result = pd.merge(original_df, scraped_df, on='Model', how='left')
"""

if __name__ == "__main__":
    print("Fix script for KeyError: 'Model' in pandas merge")
    print("Import this module and use safe_merge() or ensure_model_column() functions")
    print("\nExample:")
    print("  from fix_merge_issue import safe_merge")
    print("  result = safe_merge(df1, df2, on='Model')")






