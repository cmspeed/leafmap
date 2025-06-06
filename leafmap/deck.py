import os
from . import common
from . import examples
from . import osm
from .leafmap import basemaps

from typing import Optional

from .common import (
    add_crs,
    basemap_xyz_tiles,
    cog_bands,
    cog_bounds,
    cog_center,
    cog_tile,
    convert_lidar,
    create_legend,
    csv_to_df,
    csv_to_geojson,
    csv_to_shp,
    download_file,
    download_from_url,
    download_ned,
    gdf_to_geojson,
    geojson_to_pmtiles,
    get_api_key,
    get_census_dict,
    image_comparison,
    image_to_numpy,
    map_tiles_to_geotiff,
    netcdf_to_tif,
    numpy_to_cog,
    planet_monthly_tiles,
    planet_quarterly_tiles,
    planet_tiles,
    plot_raster,
    plot_raster_3d,
    pmtiles_metadata,
    pmtiles_style,
    read_lidar,
    read_netcdf,
    read_raster,
    read_rasters,
    save_colorbar,
    search_qms,
    search_xyz_services,
    set_api_key,
    show_html,
    show_youtube_video,
    stac_assets,
    stac_bands,
    stac_bounds,
    stac_center,
    stac_info,
    stac_search,
    stac_stats,
    stac_tile,
    start_server,
    vector_to_gif,
    view_lidar,
    write_lidar,
    zonal_stats,
)

try:
    import pydeck as pdk

except ImportError:
    raise ImportError(
        "pydeck needs to be installed to use this module. Use 'pip install pydeck' to install the package. See https://deckgl.readthedocs.io/en/latest/installation.html for more details."
    )


class Layer(pdk.Layer):
    """Configures a deck.gl layer for rendering on a map. Parameters passed here will be specific to the particular deck.gl layer that you are choosing to use.
    Please see the deck.gl Layer catalog (https://deck.gl/docs/api-reference/layers) to determine the particular parameters of your layer.
    You are highly encouraged to look at the examples in the pydeck documentation.
    """

    def __init__(self, type, data=None, id=None, use_binary_transport=None, **kwargs):
        """Initialize a Layer object.

        Args:
            type (str):  Type of layer to render, e.g., HexagonLayer. See deck.gl Layer catalog (https://deck.gl/docs/api-reference/layers)
            data (str, optional): Unique name for layer. Defaults to None.
            id (str | dict | pandas.DataFrame, optional): Either a URL of data to load in or an array of data. Defaults to None.
            use_binary_transport (bool, optional): Boolean indicating binary data. Defaults to None.
        """
        super().__init__(type, data, id, use_binary_transport, **kwargs)


class Map(pdk.Deck):
    """The Map class inherits pydeck.Deck.

    Returns:
        object: pydeck.Deck object.
    """

    def __init__(self, center=(20, 0), zoom=1.2, **kwargs):
        """Initialize a Map object.

        Args:
            center (tuple, optional): Center of the map in the format of (lat, lon). Defaults to (20, 0).
            zoom (int, optional): The map zoom level. Defaults to 1.2.
        """
        if "initial_view_state" not in kwargs:
            kwargs["initial_view_state"] = pdk.ViewState(
                latitude=center[0], longitude=center[1], zoom=zoom
            )

        if "map_style" not in kwargs:
            kwargs["map_style"] = "light"

        super().__init__(**kwargs)

    def add_layer(self, layer, layer_name: Optional[str] = None, **kwargs):
        """Add a layer to the map.

        Args:
            layer (pydeck.Layer): A pydeck Layer object.
        """

        try:
            if isinstance(layer, str) and layer.startswith("http"):
                pdk.settings.custom_libraries = [
                    {
                        "libraryName": "MyTileLayerLibrary",
                        "resourceUri": "https://cdn.jsdelivr.net/gh/giswqs/pydeck_myTileLayer@master/dist/bundle.js",
                    }
                ]
                layer = pdk.Layer("MyTileLayer", layer, id=layer_name)

            self.layers.append(layer)
        except Exception as e:
            raise Exception(e)

    def add_basemap(self, basemap: str = "HYBRID"):
        """Adds a basemap to the map.

        Args:
            basemap (str): Can be one of string from pydeck_basemaps. Defaults to 'HYBRID'.
        """
        import xyzservices

        try:
            if isinstance(basemap, xyzservices.TileProvider):
                name = basemap.name
                url = basemap.build_url()
                self.add_layer(url, name)

            elif basemap in basemaps:
                # Use pydeck_myTileLayer from https://github.com/agressin/pydeck_myTileLayer
                pdk.settings.custom_libraries = [
                    {
                        "libraryName": "MyTileLayerLibrary",
                        "resourceUri": "https://cdn.jsdelivr.net/gh/agressin/pydeck_myTileLayer@master/dist/bundle.js",
                    }
                ]

                layer = pdk.Layer("MyTileLayer", basemaps[basemap].url, basemap)

                self.add_layer(layer)

            else:
                print(
                    "Basemap can only be one of the following:\n  {}".format(
                        "\n  ".join(basemaps.keys())
                    )
                )

        except Exception:
            raise ValueError(
                "Basemap can only be one of the following:\n  {}".format(
                    "\n  ".join(basemaps.keys())
                )
            )

    def add_gdf(
        self,
        gdf,
        layer_type="GeoJsonLayer",
        layer_name: Optional[str] = None,
        random_color_column: Optional[str] = None,
        **kwargs,
    ):
        """Adds a GeoPandas GeoDataFrame to the map.

        Args:
            gdf (GeoPandas.GeoDataFrame): The GeoPandas GeoDataFrame to add to the map.
            layer_type (str, optional): The layer type to be used. Defaults to "GeoJsonLayer".
            layer_name (str, optional): The layer name to be used. Defaults to None.
            random_color_column (str, optional): The column name to use for random color. Defaults to None.

        Raises:
            TypeError: gdf must be a GeoPandas GeoDataFrame.
        """

        try:
            import geopandas as gpd

            if not isinstance(gdf, gpd.GeoDataFrame):
                raise TypeError("gdf must be a GeoPandas GeoDataFrame.")

            if layer_name is None:
                layer_name = "layer_" + common.random_string(3)

            if "layer_type" == "GeoJsonLayer":
                if "pickable" not in kwargs:
                    kwargs["pickable"] = True
                if "opacity" not in kwargs:
                    kwargs["opacity"] = 0.5
                if "stroked" not in kwargs:
                    kwargs["stroked"] = True
                if "filled" not in kwargs:
                    kwargs["filled"] = True
                if "extruded" not in kwargs:
                    kwargs["extruded"] = False
                if "wireframe" not in kwargs:
                    kwargs["wireframe"] = True
                if "get_line_color" not in kwargs:
                    kwargs["get_line_color"] = [0, 0, 0]
                if "get_line_width" not in kwargs:
                    kwargs["get_line_width"] = 2
                if "line_width_min_pixels" not in kwargs:
                    kwargs["line_width_min_pixels"] = 1

            if random_color_column is not None:
                if random_color_column not in gdf.columns.values.tolist():
                    raise ValueError(
                        "The random_color_column provided does not exist in the vector file."
                    )
                color_lookup = pdk.data_utils.assign_random_colors(
                    gdf[random_color_column]
                )
                gdf["color"] = gdf.apply(
                    lambda row: color_lookup.get(row[random_color_column]), axis=1
                )
                kwargs["get_fill_color"] = "color"

            layer = pdk.Layer(
                layer_type,
                gdf,
                id=layer_name,
                **kwargs,
            )
            self.add_layer(layer)

        except Exception as e:
            raise Exception(e)

    def add_vector(
        self,
        data: str,
        layer_type: str = "GeoJsonLayer",
        layer_name: Optional[str] = None,
        random_color_column: Optional[str] = None,
        **kwargs,
    ):
        """Adds a vector file to the map.

        Args:
            data (str): The input file path to the vector dataset.
            layer_type (str, optional): The layer type to be used. Defaults to "GeoJsonLayer".
            layer_name (str, optional): The layer name to be used. Defaults to None.
            random_color_column (str, optional): The column name to use for random color. Defaults to None.

        Raises:
            FileNotFoundError: The provided vector file could not be found.
        """

        try:
            import geopandas as gpd
            import fiona

            if isinstance(data, str):
                if not data.startswith("http"):
                    data = os.path.abspath(data)
                    if data.endswith(".zip"):
                        data = "zip://" + data

                if data.endswith(".kml"):
                    fiona.drvsupport.supported_drivers["KML"] = "rw"
                    gdf = gpd.read_file(data, driver="KML")
                else:
                    gdf = gpd.read_file(data)
            else:
                gdf = data

            self.add_gdf(gdf, layer_type, layer_name, random_color_column, **kwargs)

        except Exception as e:
            raise Exception(e)

    def add_geojson(
        self,
        filename: str,
        layer_name: Optional[str] = None,
        random_color_column: Optional[str] = None,
        **kwargs,
    ):
        """Adds a GeoJSON file to the map.

        Args:
            filename (str): The input file path to the vector dataset.
            layer_name (str, optional): The layer name to be used. Defaults to None.
            random_color_column (str, optional): The column name to use for random color. Defaults to None.

        Raises:
            FileNotFoundError: The provided vector file could not be found.
        """
        self.add_vector(filename, layer_name, random_color_column, **kwargs)

    def add_shp(
        self,
        filename: str,
        layer_name: Optional[str] = None,
        random_color_column: Optional[str] = None,
        **kwargs,
    ):
        """Adds a shapefile to the map.

        Args:
            filename (str): The input file path to the vector dataset.
            layer_name (str, optional): The layer name to be used. Defaults to None.
            random_color_column (str, optional): The column name to use for random color. Defaults to None.

        Raises:
            FileNotFoundError: The provided vector file could not be found.
        """
        self.add_vector(filename, layer_name, random_color_column, **kwargs)

    def add_kml(
        self,
        filename: str,
        layer_name: Optional[str] = None,
        random_color_column: Optional[str] = None,
        **kwargs,
    ):
        """Adds a KML file to the map.

        Args:
            filename (str): The input file path to the vector dataset.
            layer_name (str, optional): The layer name to be used. Defaults to None.
            random_color_column (str, optional): The column name to use for random color. Defaults to None.

        Raises:
            FileNotFoundError: The provided vector file could not be found.
        """
        self.add_vector(filename, layer_name, random_color_column, **kwargs)
