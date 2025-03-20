import numpy as np
import scipy.stats as stats

def calculate_statistics(data):
    import numpy as np
    from scipy import stats

    data = np.array(data, dtype=np.float64)
    data_nonan = data[~np.isnan(data)]  # Удаляем NaN
    n = len(data_nonan)
    n_obs = len(data)
    n_miss = n_obs - n

    if n == 0:
        return {"N": 0, "NMiss": n_miss, "NObs": n_obs}

    mean = np.mean(data_nonan)
    if n > 1:
        sd = np.std(data_nonan, ddof=1)
        se = sd / np.sqrt(n)
        variance = np.var(data_nonan, ddof=1)
        cv_percent = (sd / mean * 100) if mean != 0 else np.nan
    else:
        sd = se = variance = cv_percent = None

    min_val, median, max_val = np.min(data_nonan), np.median(data_nonan), np.max(data_nonan)
    range_val = max_val - min_val

    # Геометрические параметры (если есть хотя бы один ноль — все None)
    if np.any(data_nonan == 0):
        mean_log = sd_log = geometric_mean = geometric_sd = geometric_cv_percent = None
    else:
        data_pos = data_nonan[data_nonan > 0]  # Берем только положительные значения
        if len(data_pos) > 1:
            mean_log = np.mean(np.log(data_pos))
            sd_log = np.std(np.log(data_pos), ddof=1)
            geometric_mean = np.exp(mean_log)
            geometric_sd = np.exp(sd_log)
            geometric_cv_percent = (np.sqrt(np.exp(sd_log**2) - 1)) * 100
        elif len(data_pos) == 1:
            mean_log = np.log(data_pos[0])
            sd_log = geometric_sd = geometric_cv_percent = None
            geometric_mean = np.exp(mean_log)
        else:
            mean_log = sd_log = geometric_mean = geometric_sd = geometric_cv_percent = None

    if n > 1:
        if sd == 0:
            ci_95_ind_lower = ci_95_ind_upper = mean
            ci_95_mean_lower = ci_95_mean_upper = mean
        else:
            ci_95_ind = stats.t.interval(0.95, df=n - 1, loc=mean, scale=sd)
            ci_95_ind_lower, ci_95_ind_upper = ci_95_ind

            ci_95_mean = stats.t.interval(0.95, df=n - 1, loc=mean, scale=se)
            ci_95_mean_lower, ci_95_mean_upper = ci_95_mean
    else:
        ci_95_ind_lower = ci_95_ind_upper = None
        ci_95_mean_lower = ci_95_mean_upper = None

    if n > 1:
        alpha = 0.05
        df = n - 1

        chi2_upper = stats.chi2.ppf(1 - alpha / 2, df)
        chi2_lower = stats.chi2.ppf(alpha / 2, df)

        ci_95_var_lower = (df * variance) / chi2_upper if chi2_upper > 0 else np.nan
        ci_95_var_upper = (df * variance) / chi2_lower if chi2_lower > 0 else np.nan

        t_value = stats.t.ppf(1 - alpha / 2, df)

        if mean_log is not None and sd_log is not None:
            ci_95_geo = (np.exp(mean_log - t_value * sd_log), np.exp(mean_log + t_value * sd_log)) if sd_log > 0 else (geometric_mean, geometric_mean)
            ci_95_geo_mean_lower = np.exp(mean_log - t_value * sd_log / np.sqrt(n)) if sd_log > 0 else geometric_mean
            ci_95_geo_mean_upper = np.exp(mean_log + t_value * sd_log / np.sqrt(n)) if sd_log > 0 else geometric_mean
        else:
            ci_95_geo = (None, None)
            ci_95_geo_mean_lower = ci_95_geo_mean_upper = None
    else:
        ci_95_var_lower = ci_95_var_upper = np.nan
        ci_95_geo = (None, None)
        ci_95_geo_mean_lower = ci_95_geo_mean_upper = None

    # Коррекция вычисления percentiles
    if n < 3:
        percentiles = np.percentile(data_nonan, [1, 2.5, 5, 10, 25, 50, 75, 90, 95, 97.5, 99], method="nearest")
        percentiles[5] = np.median(data_nonan)  # P50 вычисляем отдельно
    else:
        percentiles = np.percentile(data_nonan, [1, 2.5, 5, 10, 25, 50, 75, 90, 95, 97.5, 99], method="nearest")

    iqr = percentiles[6] - percentiles[4]  # P75 - P25

    return {
        "N": n, "NMiss": n_miss, "NObs": n_obs, "Mean": mean, "SD": sd, "SE": se,
        "Variance": variance, "CVPercent": cv_percent, "Min": min_val, "Median": median, "Max": max_val,
        "Range": range_val, "MeanLog": mean_log, "SDLog": sd_log, "GeometricMean": geometric_mean,
        "GeometricSD": geometric_sd, "GeometricCVPercent": geometric_cv_percent,
        "CI95PercentLower": ci_95_ind_lower, "CI95PercentUpper": ci_95_ind_upper,
        "CI95PercentLowerMean": ci_95_mean_lower, "CI95PercentUpperMean": ci_95_mean_upper,
        "CI95PercentLowerVar": ci_95_var_lower, "CI95PercentUpperVar": ci_95_var_upper,
        "CIGEO95PercentLower": ci_95_geo[0], "CIGEO95PercentUpper": ci_95_geo[1],
        "CI95PercentLowerGEOMean": ci_95_geo_mean_lower, "CI95PercentUpperGEOMean": ci_95_geo_mean_upper,
        "P1": percentiles[0], "P2.5": percentiles[1], "P5": percentiles[2], "P10": percentiles[3],
        "P25": percentiles[4], "P50": percentiles[5], "P75": percentiles[6], "P90": percentiles[7],
        "P95": percentiles[8], "P97.5": percentiles[9], "P99": percentiles[10], "IQR": iqr
    }
