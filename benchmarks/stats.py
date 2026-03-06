"""Statistical helpers for benchmark analysis."""

import math
from typing import List, Tuple

try:
    import scipy.stats as stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

def trimmed_mean(data: List[float], trim_percent: float = 0.2) -> float:
    """Calculate the trimmed mean, discarding outliers.
    
    If data has < 3 elements, returns regular mean.
    If trim_percent=0.2, discards top 20% and bottom 20%.
    """
    if not data:
        return 0.0
        
    n = len(data)
    if n < 3:
        return sum(data) / n
        
    sorted_data = sorted(data)
    trim_count = int(n * trim_percent)
    
    # Ensure we don't trim everything
    if trim_count * 2 >= n:
        trim_count = (n - 1) // 2
        
    trimmed_data = sorted_data[trim_count:n - trim_count]
    return sum(trimmed_data) / len(trimmed_data)

def confidence_interval(data: List[float], confidence: float = 0.95) -> Tuple[float, float, float]:
    """Calculate the mean and confidence interval.
    
    Returns: (mean, lower_bound, upper_bound)
    """
    if not data:
        return 0.0, 0.0, 0.0
        
    n = len(data)
    mean = sum(data) / n
    
    if n < 2:
        return mean, mean, mean
        
    variance = sum((x - mean) ** 2 for x in data) / (n - 1)
    std_dev = math.sqrt(variance)
    standard_error = std_dev / math.sqrt(n)
    
    if HAS_SCIPY:
        # Use t-distribution for small samples
        h = standard_error * stats.t.ppf((1 + confidence) / 2., n-1)
    else:
        # Fall back to z-score approximation (1.96 for 95%)
        z = 1.96 if confidence == 0.95 else 2.576 # 99%
        h = standard_error * z
        
    return mean, mean - h, mean + h

def wilcoxon_test(data_a: List[float], data_b: List[float]) -> Tuple[float, float]:
    """Perform Wilcoxon signed-rank test for paired samples.
    
    Returns: (statistic, p_value)
    """
    if not HAS_SCIPY or len(data_a) != len(data_b) or len(data_a) < 5:
        return 0.0, 1.0
        
    try:
        stat, p = stats.wilcoxon(data_a, data_b)
        return float(stat), float(p)
    except Exception:
        return 0.0, 1.0

def cohens_d(data_a: List[float], data_b: List[float]) -> float:
    """Calculate Cohen's d effect size."""
    n1, n2 = len(data_a), len(data_b)
    if n1 < 2 or n2 < 2:
        return 0.0
        
    mean1, mean2 = sum(data_a)/n1, sum(data_b)/n2
    
    var1 = sum((x - mean1) ** 2 for x in data_a) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in data_b) / (n2 - 1)
    
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    if pooled_var == 0:
        return 0.0
        
    return (mean1 - mean2) / math.sqrt(pooled_var)
