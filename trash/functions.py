def adf(series_to_try):
    # Code written by Joseph Nelson.
    """
    a wrapper around the Augmented Dickey-Fuller test to provide both results and context for the output.
    """
    import pandas as pd
    from statsmodels.tsa.stattools import adfuller
    
    dftest = adfuller(series_to_try)
    result = pd.Series(dftest[0:2], index=['Test Statistic','p-value'])
    return result

def acf_pacf(series_to_plot, n_lag):
    
    """
    Plot ACF & PACF
    """
    from statsmodels.graphics.tsaplots import plot_acf
    from statsmodels.graphics.tsaplots import plot_pacf
    import matplotlib.pyplot as plt
    
    plot_acf(series_to_plot, lags = n_lag);
    plt.ylabel('autocorrelation')
    plt.xlabel('lags');

    plot_pacf(series_to_plot, lags = n_lag);
    plt.ylabel('partial autocorrelation')
    plt.xlabel('lags');
    
def evaluate(data_to_evaluate, residual, title_string = 'Residual Plot', figure_size = (12,5)):

    """
    make residual graphs and print out MSE 
    """
    import numpy as np
    import matplotlib.pyplot as plt

    plt.figure(figsize = figure_size)
    plt.scatter(data_to_evaluate.index, residual)
    plt.title(title_string, fontsize = 20)
    plt.ylabel('Residual', fontsize = 20)
    plt.xlabel('Date', fontsize = 20)
    plt.xticks(fontsize = 11)
    plt.yticks(fontsize = 11)
    plt.axhline(0, color='red')

    return {"root mean square error": np.sqrt(sum(np.square(residual)) / len(residual))}