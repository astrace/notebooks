import bisect
import numpy as np
import pandas as pd
import re
from datetime import datetime

import pylunar
mi = pylunar.MoonInfo((51, 30, 36), (0, 7, 5)) # London, UK

SECONDS_IN_DAY = 86400


def clean_data(df):
    # clean ticker symbol
    df['ticker'] = [tkr.split('|')[0] for tkr in df['ticker']]

    # remove rows where market cap or volume is 0
    for col in ['market_caps', 'total_volumes']:
        print('Removing {} rows where `{}` == 0'.format(
            (df[col] == 0).sum(), col
        ))
        df = df[df[col] != 0]
        
    # the data *should* contain consecutive days
    # sometimes this data is missing, so we put NaNs in place
    # this makes later computations much simpler
    def _fill_missing(df):
        df.sort_values('unixtime', inplace=True)
        ts_start = df.iloc[0].unixtime
        ts_end = df.iloc[-1].unixtime
        tss = range(ts_start, ts_end, SECONDS_IN_DAY)
        missing = set(tss) - set(df.unixtime)
        data = []
        for ts in missing:
            data.append([
                ts,
                datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
                df.iloc[0].ticker, np.nan, np.nan, np.nan
            ])
        return pd.DataFrame(data, columns=df.columns)

    print("Fill missing dates with NaNs.")
    df = pd.concat([
        df.groupby('ticker').apply(_fill_missing).reset_index(drop=True),
        df
    ]).reset_index(drop=True)

    print("Sort by marketcap.")
    # get latest marketcaps and sort tickers by that,
    # preseving unixtime sorting
    custom_dict = {
        v: k
        for (k, v) in enumerate(
            df.groupby('ticker').last().total_volumes.sort_values(ascending=False).index
        )
    }
    df = df.sort_values(
        by='ticker',
        key=lambda x: x.map(custom_dict)
    ).groupby('ticker', sort=False).apply(
        lambda x: x.sort_values('unixtime')
    ).reset_index(drop=True)

    return df


def moon_phase_data(df):
    def _moon_phase(date_string):
        # example data string:
        # "2012-06-19 14:08:00"
        mi.update(tuple(map(int, re.split("-|\s+|:", date_string))))
        return mi.fractional_phase()

    moon_phases = df['date'].apply(_moon_phase)
    s = (moon_phases.shift(1) > moon_phases) & (moon_phases.shift(-1) > moon_phases)
    new_moon_idxs = s.index[s]

    def _moon_cycle(idx):
        return bisect.bisect(new_moon_idxs, idx)

    def _day_after_new_moon(idx):
        nearest_new_moon = new_moon_idxs[_moon_cycle(idx) - 1]
        result = idx - nearest_new_moon
        if result >= 0:
            return result
        return 30 - (new_moon_idxs[0] - idx)

    s1 = df.apply(lambda row: _moon_cycle(row.name),axis=1)
    s2 = df.apply(lambda row: _day_after_new_moon(row.name), axis=1)
    
    return pd.DataFrame({'moon_cycle': s1, 'days_after_new_moon': s2})


def augment_data(df):
    return df.join(df.groupby('ticker').apply(moon_phase_data))

def style_table(df):
    
    # TODO: hide this code; it's just styling stuff; code hidden by default

    ###
    multiindex = pd.MultiIndex.from_product([
          ['14 Day', '30 Day', '60 Day'],
          ['Cumulative', 'Mean Daily Log'],
          ['coef', 't', 'P>|t|']
    ])

    s = df.style.format(formatter={
        t:(
            "{:.1f}" if t[2] == 't'
            else "{:.4f}" if t[2] == 'P>|t|'
            else "{:.4f}" if t[1] == 'Mean Daily Log'
            else "{:.2f}"
        )
        for t in multiindex
    })

    s.columns = pd.MultiIndex.from_product([
      ['14 Day', '30 Day', '60 Day'],
      ['Cumulative', 'Mean Daily Log'],
      ['coef', 't', 'P>|t|']
    ], names=['Window:', 'Return:', ''])

    s.set_table_styles([
        {'selector': '.index_name', 'props': 'font-weight:normal; font-weight: normal;'},
        {'selector': 'th.row_heading', 'props': 'font-weight:bold; text-align: center;'},
        {'selector': 'th.col_heading', 'props': 'text-align: center;'},
        {'selector': 'th.col_heading.level0', 'props': 'font-size: 1.5em; border-bottom: 1px solid darkgrey;'},
        {'selector': 'th.col_heading.level1', 'props': 'font-size: 1.2em; border-bottom: 1px solid darkgrey;'},
        {'selector': 'th.col_heading.level2', 'props': 'font-size: 1.2em; border-bottom: 1px solid darkgrey;'},
        {'selector': 'td', 'props': 'text-align: center; font-weight: normal;'},
        {'selector': 'th:not(.index_name)', 'props': 'background-color: black; color: white;'}
    ])

    s.set_table_styles({
        ('30 Day', 'Cumulative', 'coef'): [
            {'selector': 'th', 'props': 'border-left: 2px solid white'},
            {'selector': 'td', 'props': 'border-left: 2px solid black'}
        ],
        ('60 Day', 'Cumulative', 'coef'): [
            {'selector': 'th', 'props': 'border-left: 2px solid white'},
            {'selector': 'td', 'props': 'border-left: 2px solid black'}
        ],
        ('14 Day', 'Mean Daily Log', 'coef'): [
            {'selector': 'td', 'props': 'border-left: 1px solid black'}
        ],
        ('30 Day', 'Mean Daily Log', 'coef'): [
            {'selector': 'td', 'props': 'border-left: 1px solid black'}
        ],
        ('60 Day', 'Mean Daily Log', 'coef'): [
            {'selector': 'td', 'props': 'border-left: 1px solid black'}
        ]
    }, overwrite=False, axis=0)

    def highlight_pvalues(s):
        def _color(pvalue):
            if pvalue < 0.001:
                return "FCF947"
            if pvalue < 0.01:
                return "FDFA75"
            if pvalue < 0.05:
                return "FEFDBA"
            if pvalue < 0.1:
                return "FFFEE8"
            else:
                return ""
        props = []
        for x in ['14 Day', '30 Day', '60 Day']:
            for y in ['Cumulative', 'Mean Daily Log']:
                pvalue = s[x, y, 'P>|t|']
                props.extend(['background-color:#{}'.format(_color(pvalue))] * 3)
        return props

    return s.apply(highlight_pvalues, axis=1)
    
