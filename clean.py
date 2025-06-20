

import pandas as pd
import numpy as np



file_path = 'data/600K US Housing Properties.csv'
df = pd.read_csv(file_path, low_memory=False)



def remove_duplicate_listings(df):

    return df.drop_duplicates(subset=['property_url', 'property_id'])
df = remove_duplicate_listings(df)



def drop_unwanted_columns(df):

    columns_to_drop = ['apartment', 'listing_age', 'year_build', 'total_num_units', 
                       'agent_phone', 'agent_name', 'broker_id']
    return df.drop(columns=columns_to_drop, errors='ignore')
df = drop_unwanted_columns(df)



def fill_missing_street_names(df):

    # Step 1: Fill using mode within 'postcode'
    df['street_name'] = df['street_name'].fillna(
        df.groupby('postcode')['street_name'].transform(lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan)
    )

    # Step 2: Fill using mode within 'city'
    df['street_name'] = df['street_name'].fillna(
        df.groupby('city')['street_name'].transform(lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan)
    )

    # Step 3: Fill with overall mode if still missing
    if df['street_name'].isnull().any():
        overall_mode = df['street_name'].mode().iloc[0]
        df['street_name'].fillna(overall_mode, inplace=True)

    return df
df= fill_missing_street_names(df)



def fill_missing_city_state(df):

    # Fill city with its overall mode
    if df['city'].isnull().any():
        city_mode = df['city'].mode().iloc[0]
        df['city'].fillna(city_mode, inplace=True)

    # Fill state with its overall mode
    if df['state'].isnull().any():
        state_mode = df['state'].mode().iloc[0]
        df['state'].fillna(state_mode, inplace=True)

    return df
df = fill_missing_city_state(df)



def fill_missing_coordinates_by_location(df):
    """
    Fills missing 'latitude' and 'longitude' values using:
    1. Mode by 'postcode'
    2. Mode by 'city' (fallback)

    Parameters:
        df (pd.DataFrame): DataFrame containing 'latitude', 'longitude', 'postcode', and 'city'

    Returns:
        pd.DataFrame: Updated DataFrame with missing coordinates filled
    """
    # Step 1: Fill latitude using postcode mode
    df['latitude'] = df['latitude'].fillna(
        df.groupby('postcode')['latitude'].transform(
            lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan
        )
    )

    # Step 2: Fill longitude using postcode mode
    df['longitude'] = df['longitude'].fillna(
        df.groupby('postcode')['longitude'].transform(
            lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan
        )
    )

    # Step 3: Fallback to city-level mode
    df['latitude'] = df['latitude'].fillna(
        df.groupby('city')['latitude'].transform(
            lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan
        )
    )
    df['longitude'] = df['longitude'].fillna(
        df.groupby('city')['longitude'].transform(
            lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan
        )
    )
    return df
df = fill_missing_coordinates_by_location(df)



def remove_invalid_coordinates(df):
    """
    Removes rows with invalid latitude or longitude values.
    Latitude must be between -90 and 90.
    Longitude must be between -180 and 180.

    Parameters:
        df (pd.DataFrame): Input DataFrame with 'latitude' and 'longitude' columns.

    Returns:
        pd.DataFrame: Cleaned DataFrame with only valid coordinates.
    """
    # Define valid coordinate range
    valid_mask = df['latitude'].between(-90, 90) & df['longitude'].between(-180, 180)

    # Report and remove invalid rows
    invalid_count = (~valid_mask).sum()
    if invalid_count > 0:
        print(f"Removed {invalid_count} rows with invalid latitude or longitude.")
    else:
        print("All coordinates are within valid range.")

    # Return only valid rows
    return df[valid_mask].copy()
df=remove_invalid_coordinates(df)



def fill_missing_postcodes(df):
    """
    Fills missing postcode values by:
    1. Using the mode of postcode within the same city.
    2. If still missing, uses the mode within the same state.
    3. Prints how many postcodes were still missing (if any).

    Parameters:
        df (pd.DataFrame): The input DataFrame with 'postcode', 'city', and 'state' columns.

    Returns:
        pd.DataFrame: Updated DataFrame with missing postcodes filled where possible.
    """
    # Step 1: Fill with mode by city
    df['postcode'] = df['postcode'].fillna(
        df.groupby('city')['postcode'].transform(lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan)
    )

    # Step 2: Fill remaining with mode by state
    df['postcode'] = df['postcode'].fillna(
        df.groupby('state')['postcode'].transform(lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan)
    )
    return df

df=fill_missing_postcodes(df)



def fill_lot_beds_baths(df):
    """
    For properties of type 'LOT', fills missing values in bedroom_number and bathroom_number with 0.

    Parameters:
        df (pd.DataFrame): The input DataFrame with 'property_type', 'bedroom_number', and 'bathroom_number'.

    Returns:
        pd.DataFrame: Updated DataFrame with LOT bedrooms/bathrooms filled as 0.
    """
    lot_mask = df['property_type'] == 'LOT'

    # Fill missing values with 0 only for 'LOT' property type
    df.loc[lot_mask, 'bedroom_number'] = df.loc[lot_mask, 'bedroom_number'].fillna(0)
    df.loc[lot_mask, 'bathroom_number'] = df.loc[lot_mask, 'bathroom_number'].fillna(0)
    return df
df = fill_lot_beds_baths(df)



def fill_beds_baths_by_property_type(df):
    """
    For all non-LOT property types, fills missing bedroom_number and bathroom_number
    using the median values grouped by property_type.

    Parameters:
        df (pd.DataFrame): The input DataFrame with 'property_type', 'bedroom_number', and 'bathroom_number'.

    Returns:
        pd.DataFrame: Updated DataFrame with missing values filled by type-wise median.
    """
    # Exclude LOT properties
    non_lot_mask = df['property_type'] != 'LOT'

    # Fill bedroom_number
    df.loc[non_lot_mask, 'bedroom_number'] = df.loc[non_lot_mask].groupby('property_type')['bedroom_number'].transform(
        lambda x: x.fillna(x.median())
    )

    # Fill bathroom_number
    df.loc[non_lot_mask, 'bathroom_number'] = df.loc[non_lot_mask].groupby('property_type')['bathroom_number'].transform(
        lambda x: x.fillna(x.median())
    )
    return df
df = fill_beds_baths_by_property_type(df)


# In[129]:


df.isnull().sum()


# In[130]:


def fill_price_per_unit(df):
    """
    Fills missing values in the 'price_per_unit' column:
    1. First by calculating price / living_space (if both are available).
    2. Then by using the median price_per_unit grouped by property_type.

    Parameters:
        df (pd.DataFrame): DataFrame containing 'price', 'living_space', 'price_per_unit', 'property_type'.

    Returns:
        pd.DataFrame: Updated DataFrame with filled 'price_per_unit'.
    """
    # Step 1: Calculate price_per_unit from price / living_space
    missing_ppu = df['price_per_unit'].isnull()

    df.loc[missing_ppu, 'price_per_unit'] = df.loc[missing_ppu].apply(
        lambda row: row['price'] / row['living_space']
        if pd.notnull(row['price']) and pd.notnull(row['living_space']) and row['living_space'] != 0
        else np.nan,
        axis=1
    )

    # Step 2: Fill remaining with median by property_type
    df['price_per_unit'] = df['price_per_unit'].fillna(
        df.groupby('property_type')['price_per_unit'].transform(lambda x: x.median())
    )

    return df
df = fill_price_per_unit(df)


# In[131]:


def set_living_space_for_lots(df):
    """
    Sets missing 'living_space' to 0 for properties with type 'LOT',
    since vacant land should not have built area.

    Parameters:
        df (pd.DataFrame): The input DataFrame with 'property_type' and 'living_space'.

    Returns:
        pd.DataFrame: Updated DataFrame with 'living_space' filled for LOTs.
    """
    lot_mask = (df['property_type'] == 'LOT') & (df['living_space'].isnull())
    df.loc[lot_mask, 'living_space'] = 0
    return df
df = set_living_space_for_lots(df)


# In[132]:


def fill_living_space_by_property_type(df):
    """
    Fills missing 'living_space' for non-LOT properties using median per property_type.

    Parameters:
        df (pd.DataFrame): The input DataFrame with 'property_type' and 'living_space'.

    Returns:
        pd.DataFrame: Updated DataFrame with filled 'living_space'.
    """
    # Only for non-LOT properties
    non_lot_mask = df['property_type'] != 'LOT'

    # Fill missing values with group-wise median
    df.loc[non_lot_mask, 'living_space'] = df.loc[non_lot_mask].groupby('property_type')['living_space'].transform(
        lambda x: x.fillna(x.median())
    )

    return df
df = fill_living_space_by_property_type(df)


# In[133]:


def fill_land_space_for_condo_apartment(df):
    """
    Sets missing 'land_space' to 0 for properties of type CONDO and APARTMENT.

    Parameters:
        df (pd.DataFrame): The input DataFrame with 'property_type' and 'land_space'.

    Returns:
        pd.DataFrame: Updated DataFrame with missing land_space filled as 0 for applicable types.
    """
    mask = df['property_type'].isin(['CONDO', 'APARTMENT']) & df['land_space'].isnull()
    df.loc[mask, 'land_space'] = 0

    return df
df = fill_land_space_for_condo_apartment(df)


# In[134]:


def fill_land_space_by_property_type(df):
    """
    Fills missing 'land_space' for non-CONDO and non-APARTMENT properties
    using the median land_space grouped by property_type.

    Parameters:
        df (pd.DataFrame): The input DataFrame with 'property_type' and 'land_space'.

    Returns:
        pd.DataFrame: Updated DataFrame with filled 'land_space'.
    """
    # Define types that need to be filled with median (i.e., NOT condo/apartment)
    types_needing_median = ['SINGLE_FAMILY', 'MULTI_FAMILY', 'TOWNHOUSE', 'MANUFACTURED', 'LOT']

    # Filter mask
    mask = df['property_type'].isin(types_needing_median) & df['land_space'].isnull()

    # Apply median fill per property type
    df.loc[mask, 'land_space'] = df.loc[mask].groupby('property_type')['land_space'].transform(
        lambda x: x.fillna(x.median())
    )

    return df
df = fill_land_space_by_property_type(df)


# In[135]:


def fill_land_space_with_overall_median(df):
    """
    Fills all remaining missing values in 'land_space' using the overall median of the column.

    Parameters:
        df (pd.DataFrame): The input DataFrame with 'land_space'.

    Returns:
        pd.DataFrame: Updated DataFrame with all missing 'land_space' filled.
    """
    overall_median_land = df['land_space'].median()
    missing_count = df['land_space'].isnull().sum()

    df['land_space'] = df['land_space'].fillna(overall_median_land)

    return df
df = fill_land_space_with_overall_median(df)


# In[136]:


def fill_land_space_unit_with_mode(df):
    """
    Fills missing 'land_space_unit' values with the most frequent (mode) value.

    Parameters:
        df (pd.DataFrame): The input DataFrame with 'land_space_unit'.

    Returns:
        pd.DataFrame: Updated DataFrame with missing 'land_space_unit' filled.
    """
    mode_unit = df['land_space_unit'].mode()
    if not mode_unit.empty:
        fill_value = mode_unit[0]
        missing_count = df['land_space_unit'].isnull().sum()
        df['land_space_unit'] = df['land_space_unit'].fillna(fill_value)

    return df
df = fill_land_space_unit_with_mode(df)


# In[ ]:


def fill_agency_name_with_unknown(df):

    df["RunDate"] = pd.to_datetime(df["RunDate"]).dt.date

    missing_count = df['agency_name'].isnull().sum()
    df['agency_name'] = df['agency_name'].fillna("Unknown")
    return df
df = fill_agency_name_with_unknown(df)


# In[138]:


df.isnull().sum()


# In[139]:


# Define export path
export_path = '/Users/kittu/Downloads/live property search/data/cleaned_data.csv'

# Export DataFrame as CSV
df.to_csv(export_path, index=False)

print(f"Data exported successfully to:\n{export_path}")


# In[161]:


df.dtypes


# In[160]:


def convert_column_types(df):
    """
    Converts column types:
    - postcode, bedroom_number, bathroom_number to integers
    - is_owned_by_zillow to boolean

    Parameters:
        df (pd.DataFrame): Input DataFrame

    Returns:
        pd.DataFrame: Updated DataFrame with proper types
    """
    # Convert to integer safely (handle NaNs)
    for col in ['postcode', 'bedroom_number', 'bathroom_number']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Convert is_owned_by_zillow to boolean
    df['is_owned_by_zillow'] = df['is_owned_by_zillow'].astype(bool)

    return df
df = convert_column_types(df)


# In[ ]:


# !pip install mysql-connector-python


# In[165]:


import mysql.connector
from config import DB_CONFIG

def db_connection():
    """
    Create and return a MySQL database connection

    Returns:
        tuple: (connection, cursor) if successful, (None, None) if failed
    """
    try:
        # Connect to MySQL using config
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['username'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            port=DB_CONFIG['port']
        )

        if conn.is_connected():
            print("Connection established successfully!")
            cursor = conn.cursor()
            return conn, cursor
        else:
            print("Failed to connect to MySQL.")
            return None, None

    except Exception as e:
        print(f"Connection error: {e}")
        return None, None

def data_export(conn, cursor, csv_path="data/cleaned_data.csv"):
    """
    Export data from CSV to MySQL HouseData table

    Args:
        conn: MySQL connection object
        cursor: MySQL cursor object
        csv_path: Path to the CSV file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create Table (if not exists)
        create_table_query = """
        CREATE TABLE IF NOT EXISTS HouseData (
            property_id VARCHAR(100) PRIMARY KEY,
            property_url TEXT,
            address TEXT,
            street_name TEXT,
            city VARCHAR(100),
            state VARCHAR(50),
            postcode VARCHAR(20),
            latitude DOUBLE,
            longitude DOUBLE,
            price DOUBLE,
            bedroom_number INT,
            bathroom_number INT,
            price_per_unit DOUBLE,
            living_space DOUBLE,
            land_space DOUBLE,
            land_space_unit VARCHAR(20),
            property_type VARCHAR(50),
            property_status VARCHAR(50),
            RunDate DATE,
            agency_name VARCHAR(255),
            is_owned_by_zillow BOOLEAN
        );
        """
        cursor.execute(create_table_query)
        print("Table 'HouseData' is ready.")

        # Load Cleaned CSV into DataFrame
        df = pd.read_csv(csv_path)

        # Reorder columns to match SQL insert
        columns = [
            "property_id", "property_url", "address", "street_name", "city", "state", "postcode",
            "latitude", "longitude", "price", "bedroom_number", "bathroom_number",
            "price_per_unit", "living_space", "land_space", "land_space_unit",
            "property_type", "property_status", "RunDate", "agency_name", "is_owned_by_zillow"
        ]
        df = df[columns]

        # Prepare insert query
        insert_query = """
        INSERT INTO HouseData (
            property_id, property_url, address, street_name, city, state, postcode,
            latitude, longitude, price, bedroom_number, bathroom_number,
            price_per_unit, living_space, land_space, land_space_unit,
            property_type, property_status, RunDate, agency_name, is_owned_by_zillow
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        # Convert DataFrame to list of tuples (handle NaNs)
        data = df.where(pd.notnull(df), None).values.tolist()

        # Insert all rows
        cursor.executemany(insert_query, data)
        conn.commit()
        print(f"Inserted {cursor.rowcount} rows into 'HouseData' table.")

        return True

    except Exception as e:
        print(f"Data export error: {e}")
        if conn:
            conn.rollback()
        return False


if __name__ == "__main__":
    # Step 1: Fill missing postcodes
    df = fill_missing_postcodes(df)

    # Step 2: Fill beds/baths for LOT and others
    df = fill_lot_beds_baths(df)
    df = fill_beds_baths_by_property_type(df)

    # Step 3: Fill living space
    df = set_living_space_for_lots(df)
    df = fill_living_space_by_property_type(df)

    # Step 4: Fill land space
    df = fill_land_space_for_condo_apartment(df)
    df = fill_land_space_by_property_type(df)
    df = fill_land_space_with_overall_median(df)

    # Step 5: Fill land space unit
    df = fill_land_space_unit_with_mode(df)

    # Step 6: Fill agency name
    df = fill_agency_name_with_unknown(df)

    # Step 7: Fill coordinates
    df = fill_missing_coordinates_by_location(df)

    # Step 8: Remove invalid coordinates
    df = remove_invalid_coordinates(df)

    # Step 9: Fill price per unit
    df = fill_price_per_unit(df)

    # Step 10: Export to MySQL
    conn, cursor = db_connection()
    if conn and cursor:
        export_success = data_export(conn, cursor)
        cursor.close()
        conn.close()
        print("Connection closed.")
        if export_success:
            print("Data export completed successfully!")
        else:
            print("Data export failed!")
    else:
        print("Could not establish database connection.")

