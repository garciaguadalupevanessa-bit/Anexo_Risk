import pandas as pd

from src.data_loader import load_combined_data, _generate_synthetic_fallback
from src.h3_aggregator import lat_lon_to_h3, aggregate_by_h3, merge_h3_datasets


class TestH3Aggregator:
    def test_lat_lon_to_h3_returns_string(self):
        h = lat_lon_to_h3(40.0, -3.0, 4)
        assert isinstance(h, str)
        assert len(h) > 0

    def test_lat_lon_to_h3_returns_none_on_invalid(self):
        h = lat_lon_to_h3(float("nan"), float("nan"), 4)
        assert h is None

    def test_aggregate_by_h3_returns_grouped(self, small_h3_df):
        result = aggregate_by_h3(small_h3_df, res=4)
        assert isinstance(result, pd.DataFrame)
        assert "h3_index" in result.columns
        assert result.shape[0] <= small_h3_df.shape[0]

    def test_merge_h3_datasets_returns_merged(self, small_h3_df):
        datasets = [("a_", small_h3_df, {"viento": "max"})]
        result = merge_h3_datasets(datasets, res=4)
        assert isinstance(result, pd.DataFrame)
        assert "_h3_key" in result.columns or result.empty

    def test_merge_h3_datasets_empty_input(self):
        empty = pd.DataFrame(columns=["lat", "lon"])
        datasets = [("a_", empty, {})]
        assert merge_h3_datasets(datasets, res=4) is None


class TestDataLoader:
    def test_load_combined_data_returns_dataframe(self):
        df = load_combined_data()
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] > 0

    def test_load_combined_data_has_expected_columns(self):
        df = load_combined_data()
        expected = {
            "viento_max_ciclones",
            "presion_min_ciclones",
            "magnitud_max_sismo",
            "profundidad_media_sismo",
            "elevacion_volcan",
            "lat",
            "lon",
            "categoria_tormenta",
            "frecuencia_eventos_sismicos",
        }
        assert expected.issubset(set(df.columns))

    def test_load_combined_data_types_are_numeric(self):
        df = load_combined_data()
        numeric_cols = [
            "viento_max_ciclones",
            "presion_min_ciclones",
            "magnitud_max_sismo",
            "profundidad_media_sismo",
            "elevacion_volcan",
            "lat",
            "lon",
        ]
        for col in numeric_cols:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} is not numeric"

    def test_load_combined_data_no_missing_lat_lon(self):
        df = load_combined_data()
        assert df["lat"].notna().all()
        assert df["lon"].notna().all()

    def test_load_combined_data_storm_category_present(self):
        df = load_combined_data()
        assert "categoria_tormenta" in df.columns
        valid = {"TD", "TS", "C1", "C2", "C3", "C4", "C5"}
        assert df["categoria_tormenta"].isin(valid).all()


class TestSyntheticFallback:
    def test_fallback_shape(self):
        df = _generate_synthetic_fallback()
        assert df.shape == (500, 10)

    def test_fallback_has_all_columns(self):
        df = _generate_synthetic_fallback()
        expected = {
            "magnitud_max_sismo",
            "profundidad_media_sismo",
            "frecuencia_eventos_sismicos",
            "viento_max_ciclones",
            "presion_min_ciclones",
            "elevacion_volcan",
            "categoria_tormenta",
            "tipo_volcan",
            "lat",
            "lon",
        }
        assert set(df.columns) == expected

    def test_fallback_no_missing(self):
        df = _generate_synthetic_fallback()
        assert df.isnull().sum().sum() == 0

    def test_fallback_reproducible(self):
        df1 = _generate_synthetic_fallback()
        df2 = _generate_synthetic_fallback()
        assert df1.equals(df2)
