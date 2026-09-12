from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from statsmodels.tsa.holtwinters import ExponentialSmoothing


SERVER = r"NAREN"
DATABASE = "McKinsey_CFO_Intelligence"
DRIVER = "ODBC Driver 18 for SQL Server"


def get_engine():
    # Connecting to SQL Server
    if SERVER == "YOUR_SERVER_NAME":
        raise ValueError("Update SERVER at the top of this file with your SQL Server name.")

    connection_string = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    connection_url = URL.create(
        "mssql+pyodbc",
        query={"odbc_connect": connection_string},
    )

    return create_engine(connection_url)


def calculate_mape(actual, forecast):
    # Calculating forecast error
    actual = np.array(actual, dtype=float)
    forecast = np.array(forecast, dtype=float)

    valid = np.abs(actual) >= 1.0

    if valid.sum() == 0:
        return np.nan

    return np.mean(
        np.abs((actual[valid] - forecast[valid]) / actual[valid])
    ) * 100


def moving_average_forecast(series, periods=12):
    # Calculating moving average forecast
    average_value = series.tail(12).mean()
    return np.repeat(average_value, periods)


def exponential_smoothing_forecast(series, periods=12):
    # Calculating exponential smoothing forecast
    model = ExponentialSmoothing(
        series,
        trend="add",
        seasonal="add",
        seasonal_periods=12,
        initialization_method="estimated",
    )

    fitted_model = model.fit(optimized=True)
    return fitted_model.forecast(periods).values


def test_models(series):
    # Comparing forecast models
    train = series.iloc[:-12]
    test = series.iloc[-12:]

    moving_forecast = moving_average_forecast(train, 12)
    moving_mape = calculate_mape(test.values, moving_forecast)

    try:
        smoothing_forecast = exponential_smoothing_forecast(train, 12)
        smoothing_mape = calculate_mape(test.values, smoothing_forecast)
    except Exception:
        smoothing_mape = np.nan

    if pd.isna(smoothing_mape) or moving_mape <= smoothing_mape:
        selected_model = "Moving Average"
        selected_mape = moving_mape
    else:
        selected_model = "Exponential Smoothing"
        selected_mape = smoothing_mape

    forecast_accuracy = max(0, 100 - selected_mape)

    return {
        "moving_average_mape": moving_mape,
        "exponential_smoothing_mape": smoothing_mape,
        "selected_model": selected_model,
        "selected_mape": selected_mape,
        "forecast_accuracy": forecast_accuracy,
    }


def create_final_forecast(series, selected_model, periods=12):
    # Creating final forecast
    if selected_model == "Exponential Smoothing":
        try:
            forecast = exponential_smoothing_forecast(series, periods)
        except Exception:
            forecast = moving_average_forecast(series, periods)
    else:
        forecast = moving_average_forecast(series, periods)

    return forecast


def main():
    # Creating the output folder
    project_root = Path(__file__).resolve().parents[1]
    processed_folder = project_root / "data" / "processed"
    processed_folder.mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    # Loading SQL data
    features = pd.read_sql(
        "SELECT * FROM dbo.financial_features",
        engine,
    )
    business_units = pd.read_sql(
        "SELECT * FROM dbo.clean_business_units",
        engine,
    )
    budget = pd.read_sql(
        "SELECT * FROM dbo.clean_budget_forecast",
        engine,
    )

    features["period_end"] = pd.to_datetime(features["period_end"])
    budget["period_end"] = pd.to_datetime(budget["period_end"])

    # Creating monthly business unit data
    monthly = (
        features.groupby(
            ["period_end", "business_unit_id"],
            as_index=False,
        )
        .agg(
            revenue_usd_m=("revenue_usd_m", "sum"),
            ebitda_usd_m=("ebitda_usd_m", "sum"),
            free_cash_flow_usd_m=("free_cash_flow_usd_m", "sum"),
        )
        .sort_values(["business_unit_id", "period_end"])
    )

    metrics = {
        "revenue_usd_m": "revenue",
        "ebitda_usd_m": "ebitda",
        "free_cash_flow_usd_m": "fcf",
    }

    future_dates = pd.date_range(
        start="2026-01-31",
        periods=12,
        freq=pd.offsets.MonthEnd(),
    )

    forecast_rows = []
    accuracy_rows = []

    # Forecasting each business unit
    for business_unit_id in monthly["business_unit_id"].unique():
        unit_data = (
            monthly[monthly["business_unit_id"] == business_unit_id]
            .sort_values("period_end")
            .reset_index(drop=True)
        )

        unit_forecasts = {
            "business_unit_id": business_unit_id,
            "period_end": future_dates,
        }

        for metric, short_name in metrics.items():
            series = unit_data[metric].astype(float)

            model_result = test_models(series)

            final_forecast = create_final_forecast(
                series,
                model_result["selected_model"],
                12,
            )

            if metric in ["revenue_usd_m", "ebitda_usd_m"]:
                final_forecast = np.maximum(final_forecast, 0)

            unit_forecasts[f"forecast_{short_name}_usd_m"] = final_forecast
            unit_forecasts[f"{short_name}_model"] = model_result["selected_model"]

            accuracy_rows.append(
                {
                    "business_unit_id": business_unit_id,
                    "metric": short_name,
                    "moving_average_mape": round(
                        model_result["moving_average_mape"], 2
                    ),
                    "exponential_smoothing_mape": (
                        round(model_result["exponential_smoothing_mape"], 2)
                        if not pd.isna(model_result["exponential_smoothing_mape"])
                        else np.nan
                    ),
                    "selected_model": model_result["selected_model"],
                    "selected_mape": round(model_result["selected_mape"], 2),
                    "forecast_accuracy": round(
                        model_result["forecast_accuracy"], 2
                    ),
                }
            )

        unit_forecast = pd.DataFrame(unit_forecasts)
        forecast_rows.append(unit_forecast)

    forecast = pd.concat(forecast_rows, ignore_index=True)
    accuracy = pd.DataFrame(accuracy_rows)

    # Adding business unit names
    names = business_units[
        ["business_unit_id", "business_unit_name"]
    ].drop_duplicates()

    forecast = forecast.merge(
        names,
        on="business_unit_id",
        how="left",
    )

    accuracy = accuracy.merge(
        names,
        on="business_unit_id",
        how="left",
    )

    # Loading 2026 budget
    budget_2026 = budget[budget["period_end"].dt.year == 2026].copy()

    budget_2026 = (
        budget_2026.groupby(
            ["period_end", "business_unit_id"],
            as_index=False,
        )
        .agg(
            budget_revenue_usd_m=("budget_revenue_usd_m", "sum"),
            budget_ebitda_usd_m=("budget_ebitda_usd_m", "sum"),
            budget_fcf_usd_m=("budget_fcf_usd_m", "sum"),
        )
    )

    forecast = forecast.merge(
        budget_2026,
        on=["period_end", "business_unit_id"],
        how="left",
    )

    # Calculating forecast versus budget
    forecast["revenue_vs_budget_pct"] = (
        forecast["forecast_revenue_usd_m"]
        - forecast["budget_revenue_usd_m"]
    ) / forecast["budget_revenue_usd_m"]

    forecast["ebitda_vs_budget_pct"] = (
        forecast["forecast_ebitda_usd_m"]
        - forecast["budget_ebitda_usd_m"]
    ) / forecast["budget_ebitda_usd_m"]

    forecast["fcf_vs_budget_pct"] = (
        forecast["forecast_fcf_usd_m"]
        - forecast["budget_fcf_usd_m"]
    ) / forecast["budget_fcf_usd_m"].abs()

    # Rounding forecast values
    money_columns = [
        "forecast_revenue_usd_m",
        "forecast_ebitda_usd_m",
        "forecast_fcf_usd_m",
        "budget_revenue_usd_m",
        "budget_ebitda_usd_m",
        "budget_fcf_usd_m",
    ]

    forecast[money_columns] = forecast[money_columns].round(2)

    # Creating forecast budget labels
    forecast["forecast_budget_status"] = np.select(
        [
            (forecast["revenue_vs_budget_pct"] <= -0.10)
            | (forecast["ebitda_vs_budget_pct"] <= -0.15),
            (forecast["revenue_vs_budget_pct"] <= -0.05)
            | (forecast["ebitda_vs_budget_pct"] <= -0.075),
        ],
        ["Critical", "Warning"],
        default="Normal",
    )

    forecast = forecast[
        [
            "period_end",
            "business_unit_id",
            "business_unit_name",
            "forecast_revenue_usd_m",
            "forecast_ebitda_usd_m",
            "forecast_fcf_usd_m",
            "budget_revenue_usd_m",
            "budget_ebitda_usd_m",
            "budget_fcf_usd_m",
            "revenue_vs_budget_pct",
            "ebitda_vs_budget_pct",
            "fcf_vs_budget_pct",
            "forecast_budget_status",
            "revenue_model",
            "ebitda_model",
            "fcf_model",
        ]
    ]

    # Creating forecast accuracy labels
    accuracy["accuracy_status"] = np.select(
        [
            accuracy["forecast_accuracy"] >= 90,
            accuracy["forecast_accuracy"] >= 80,
        ],
        ["Strong", "Watch"],
        default="Weak",
    )

    accuracy = accuracy[
        [
            "business_unit_id",
            "business_unit_name",
            "metric",
            "moving_average_mape",
            "exponential_smoothing_mape",
            "selected_model",
            "selected_mape",
            "forecast_accuracy",
            "accuracy_status",
        ]
    ]

    # Saving forecast files
    forecast_path = processed_folder / "financial_forecast.csv"
    accuracy_path = processed_folder / "forecast_accuracy.csv"

    forecast.to_csv(forecast_path, index=False)
    accuracy.to_csv(accuracy_path, index=False)

    # Saving forecast tables
    forecast.to_sql(
        "financial_forecast",
        engine,
        schema="dbo",
        if_exists="replace",
        index=False,
    )

    accuracy.to_sql(
        "forecast_accuracy",
        engine,
        schema="dbo",
        if_exists="replace",
        index=False,
    )

    print(f"Forecast rows created: {len(forecast)}")
    print(f"Accuracy rows created: {len(accuracy)}")
    print(f"Forecast saved to: {forecast_path}")
    print(f"Accuracy saved to: {accuracy_path}")
    print("SQL table saved as: dbo.financial_forecast")
    print("SQL table saved as: dbo.forecast_accuracy")

    engine.dispose()


if __name__ == "__main__":
    main()
