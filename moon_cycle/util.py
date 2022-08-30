import pandas as pd

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
    