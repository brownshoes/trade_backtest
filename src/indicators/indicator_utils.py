def split_on_nulls(df, value_col):
    """
    Splits a DataFrame into multiple DataFrames
    whenever a null value appears in value_col.
    """
    is_null = df[value_col].isna()

    # Increment segment id whenever we hit a null
    segment_id = is_null.cumsum()

    segments = []
    for _, group in df[~is_null].groupby(segment_id):
        segments.append(group)

    return segments