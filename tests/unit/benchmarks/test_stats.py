"""Unit tests for statistical helpers."""

import pytest
from benchmarks.stats import trimmed_mean, confidence_interval, wilcoxon_test, cohens_d

def test_trimmed_mean():
    # Trimmed mean of [1, 2, 3, 4, 100] with 20% trim (top/bottom 1)
    # Should exclude 1 and 100
    data = [1, 2, 3, 4, 100]
    result = trimmed_mean(data, 0.2)
    assert result == 3.0 # (2+3+4)/3 = 9/3

def test_trimmed_mean_small_sample():
    # Less than 3 items, no trim
    data = [1, 100]
    result = trimmed_mean(data, 0.2)
    assert result == 50.5

def test_confidence_interval():
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    mean, lower, upper = confidence_interval(data, 0.95)
    
    assert mean == 3.0
    # CI should be symmetric around the mean
    assert round(mean - lower, 4) == round(upper - mean, 4)
    # With 0.95 confidence, bounds should be approx [1.037, 4.963] using t-dist or z-score
    assert lower > 0 # Should be well above 0
    assert upper < 6 # Should be below 6

def test_confidence_interval_single_item():
    data = [42.0]
    mean, lower, upper = confidence_interval(data, 0.95)
    assert mean == 42.0
    assert lower == 42.0
    assert upper == 42.0

def test_wilcoxon_different_distributions():
    # Only meaningful if scipy is installed and N >= 5
    import benchmarks.stats as stats_module
    
    if not stats_module.HAS_SCIPY:
        pytest.skip("Scipy not installed, mocking wilcoxon")
        
    group1 = [1.0, 1.1, 1.2, 1.0, 1.1]
    group2 = [5.0, 5.1, 5.2, 5.0, 5.1]
    
    stat, p_val = wilcoxon_test(group1, group2)
    
    # Very likely to be significantly different
    assert p_val < 0.1

def test_wilcoxon_identical():
    group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    stat, p_val = wilcoxon_test(group1, group1)
    # Should not be significantly different
    assert p_val > 0.1

def test_cohens_d_large_effect():
    g1 = [1.0, 2.0, 3.0, 4.0, 5.0] # mean 3.0
    g2 = [10.0, 11.0, 12.0, 13.0, 14.0] # mean 12.0
    
    # Large difference in means relative to variance
    d = cohens_d(g2, g1) 
    assert d > 2.0 # Huge effect size

def test_cohens_d_no_effect():
    g1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    d = cohens_d(g1, g1)
    assert d == 0.0
