import geopandas as gpd
import pandas as pd
import libpysal as lps
from esda.moran import Moran
from esda.moran import Moran_Local

def clusters(gdf, crs:int, col:str, alpha:float=0.15):

    """Calculates spatial clusters/outliers based on a column in a geofataframe
    
    
    Workflow:

    1.  Create a spatial weights matrix
    2.  Create a spatially lagged version of the variable of interest
    3.  Calculate global spatial autocorrelation metrics
    4.  Calculate local spatial autocorrelation (the clusters) using LISA
        (local indicators of spatial autocorrelation)
    5.  Join data to original gdf

    While the code should work for any geodataframe, the current workflow is
    based on the assumption that the data being analyzed is in a hexagonal
    grid. This makes it sensible to model neighbourhoods simply by using a k-
    nearest neighbors spatial weights matrix where k=6.

    
    Input:

    gdf     The source geodataframe, should be a hexagonal grid if using this
            script as is
    crs     A coordinate reference system, EPSG code
    col     The column with the data being modeled
    alpha   The threshold of statistical significance to be used when determing
            whether a cell is a cluster/outlier or not. A strict value would 
            be 0.05, defaults to 0.15


    The output is the original dataframe with 2 new columns:

    quadrant        The quadrant to which the observation belongs to:
                    LL = low clusters = low values surrounded by low values
                    HH = high clusters = high values surrounded by high values
                    LH = low outliers = low values surrounded by high values
                    HL = high outliers = high values surrounded by low values
    significant     Whether the quadrant information is statistically
                    significant
    """

    # Project
    gdf = gdf.to_crs(crs)
    
    # Dropna
    gdf_not_null = gdf[[col, "geometry"]].dropna()

    # Compute spatial weights and row-standardize
    weights = lps.weights.KNN.from_dataframe(gdf_not_null, k=6)
    weights.set_transform("R")
    
    # Compute spatial lag
    y = gdf_not_null[col]
    y_lag = lps.weights.lag_spatial(weights, y)
    col_lag = f"{col}_lag"
    data_lag = pd.DataFrame(data={col:y, col_lag:y_lag})

    # Global spatial autocorrelation
    mi = Moran(data_lag[col], weights)
    p_value = mi.p_sim
    print(
        "\nGlobal spatial autocorrelation:\n"
        + "Moran's I:   "
        + str(round(mi.I, 3))
        + "\np-value:     "
        + str(round(p_value, 3))
    )

    # Calculate LISA values
    lisa = Moran_Local(
        data_lag[col],
        weights,
        permutations=10000,
        #seed=1             # Use this if absolute repoducibility is needed
    )

    # identify whether each observation is significant or not
    data_lag["significant"] = lisa.p_sim < alpha

    # identify the quadrant each observation belongs to
    data_lag["quadrant"] = lisa.q
    data_lag["quadrant"] = data_lag["quadrant"].replace(
        {1:"HH", 2:"LH", 3:"LL", 4:"HL"}
    )
    
    # Print info
    print(
        "\nDistribution of clusters/outliers (quadrants):\n"
        + str(data_lag["quadrant"].sort_values().value_counts())
    )
    print(
        "\nSignificant clusters (using significance threshold "
        + str(alpha)
        + "):\n"
        + str(data_lag["significant"].value_counts())
    )

    # Merge original gdf and LISA quadrants data together
    gdf_clusters = gdf.merge(
        data_lag[["quadrant", "significant"]],
        how="left",
        left_index=True,
        right_index=True
    )

    return gdf_clusters
