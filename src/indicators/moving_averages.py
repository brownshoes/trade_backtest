import pandas_ta as ta

MOVING_AVERAGES = {
    "dema": ta.dema,
    "ema": ta.ema,
    "fwma": ta.fwma,
    "hma": ta.hma,
    "linreg": ta.linreg,
    "midpoint": ta.midpoint,
    "pwma": ta.pwma,
    "rma": ta.rma,
    "sinwma": ta.sinwma,
    "sma": ta.sma,
    "swma": ta.swma,
    "t3": ta.t3,
    "tema": ta.tema,
    "trima": ta.trima,
    "vidya": ta.vidya,
    "wma": ta.wma,
    "zlma": ta.zlma,
}

def get_ma(name: str):
    key = name.strip().lower()
    try:
        return MOVING_AVERAGES[key]
    except KeyError:
        raise ValueError(
            f"Invalid moving average '{name}'. "
            f"Available: {', '.join(MOVING_AVERAGES.keys())}"
        )
