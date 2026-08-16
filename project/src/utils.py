
import pandas as pd


def clean_column_names(df):
    """
    Clean DataFrame column names.

    Converts column names to lowercase, removes leading/trailing
    whitespace, and replaces spaces with underscores.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame.

    Returns
    -------
    pandas.DataFrame
        DataFrame with cleaned column names.
    """

    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df
def parse_date_column(df, column="date"):
    """
    Convert a DataFrame column to pandas datetime format.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame.

    column : str
        Name of the date column.

    Returns
    -------
    pandas.DataFrame
        DataFrame with parsed datetime column.
    """

    df = df.copy()

    df[column] = pd.to_datetime(df[column])

    return df