import streamlit as st
from ..config import get_text


def show_info():
    """Info page explaining all analysis methods"""
    st.title(f"💡 {get_text('info_page_title')}")

    # Introduction
    st.markdown(get_text("info_page_intro"))

    # Create tabs for different analysis methods
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
        [
            f"🛡️ {get_text('mos_tab')}",
            f"💸 {get_text('dcf_tab')}",
            f"🔟 {get_text('tencap_tab')}",
            f"⏰ {get_text('pbt_tab')}",
            f"📈 {get_text('cagr_tab')}",
            f"💳 {get_text('debt_tab')}",
            f"💰 {get_text('profitability_tab')}",
            f"🌍 {get_text('suffix_guide_title')}",
            f"💡 {get_text('usage_tab')}",
        ]
    )

    with tab1:
        st.header(f"🛡️ {get_text('mos_method_title')}")
        st.markdown(get_text("mos_description"))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(get_text("how_it_works"))
            st.markdown(get_text("mos_how_it_works"))

        with col2:
            st.subheader(get_text("when_to_use"))
            st.markdown(get_text("mos_when_to_use"))

        st.subheader(get_text("formula"))
        st.latex(r"MOS\_Price = Intrinsic\_Value \times (1 - MOS\_Rate)")
        st.markdown(get_text("mos_formula_explanation"))

    with tab2:
        st.header(f"💸 {get_text('dcf_method_title')}")
        st.markdown(get_text("dcf_description"))

        # Sub-tabs for the three DCF methods
        dcf_tab1, dcf_tab2, dcf_tab3 = st.tabs(
            ["📊 DCF fmp", "🏭 Unlevered (FCFF)", "🏦 Levered (FCFE)"]
        )

        with dcf_tab1:
            st.subheader(f"📊 {get_text('dcf_fmp_method_title')}")
            st.markdown(get_text("dcf_fmp_method_description"))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader(get_text("how_it_works"))
                st.markdown(get_text("dcf_fmp_how_it_works"))

            with col2:
                st.subheader(get_text("when_to_use"))
                st.markdown(get_text("dcf_fmp_when_to_use"))

            st.subheader(get_text("formula"))
            st.latex(r"Buy\_Price = FMP\_DCF \times (1 - MOS\_Rate)")
            st.markdown(get_text("dcf_fmp_formula_explanation"))

        with dcf_tab2:
            st.subheader(f"🏭 {get_text('dcf_unlevered_method_title')}")
            st.markdown(get_text("dcf_unlevered_method_description"))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader(get_text("how_it_works"))
                st.markdown(get_text("dcf_unlevered_how_it_works"))

            with col2:
                st.subheader(get_text("when_to_use"))
                st.markdown(get_text("dcf_unlevered_when_to_use"))

            st.subheader(get_text("formula"))
            st.latex(r"FCFF = EBIT \times (1 - Tax) + D\&A - CapEx - \Delta NWC")
            st.latex(
                r"Enterprise\_Value = \sum_{t=1}^{n} \frac{FCFF_t}{(1 + WACC)^t} + \frac{Terminal\_Value}{(1 + WACC)^n}"
            )
            st.latex(r"Equity\_Value = Enterprise\_Value - Net\_Debt")
            st.markdown(get_text("dcf_unlevered_formula_explanation"))

        with dcf_tab3:
            st.subheader(f"🏦 {get_text('dcf_levered_method_title')}")
            st.markdown(get_text("dcf_levered_method_description"))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader(get_text("how_it_works"))
                st.markdown(get_text("dcf_levered_how_it_works"))

            with col2:
                st.subheader(get_text("when_to_use"))
                st.markdown(get_text("dcf_levered_when_to_use"))

            st.subheader(get_text("formula"))
            st.latex(r"FCFE = CFO - CapEx + Net\_Borrowing")
            st.latex(
                r"Equity\_Value = \sum_{t=1}^{n} \frac{FCFE_t}{(1 + Cost\_of\_Equity)^t} + \frac{Terminal\_Value}{(1 + Cost\_of\_Equity)^n}"
            )
            st.latex(
                r"Fair\_Value\_per\_Share = \frac{Equity\_Value}{Shares\_Outstanding}"
            )
            st.markdown(get_text("dcf_levered_formula_explanation"))

    with tab3:
        st.header(f"🔟 {get_text('tencap_method_title')}")
        st.markdown(get_text("tencap_description"))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(get_text("how_it_works"))
            st.markdown(get_text("tencap_how_it_works"))

        with col2:
            st.subheader(get_text("when_to_use"))
            st.markdown(get_text("tencap_when_to_use"))

        st.subheader(get_text("formula"))
        st.latex(r"TEN\_CAP = \frac{Owner\_Earnings / Shares}{0.10}")
        st.markdown(get_text("tencap_formula_explanation"))

    with tab4:
        st.header(f"⏰ {get_text('pbt_method_title')}")
        st.markdown(get_text("pbt_description"))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(get_text("how_it_works"))
            st.markdown(get_text("pbt_how_it_works"))

        with col2:
            st.subheader(get_text("when_to_use"))
            st.markdown(get_text("pbt_when_to_use"))

        st.subheader(get_text("formula"))
        st.latex(r"Fair\_Value = \sum_{t=1}^{8} FCF \times (1 + g)^t")
        st.latex(r"PBT\_Buy\_Price = Fair\_Value \times (1 - MOS)")
        st.markdown(get_text("pbt_formula_explanation"))

    with tab5:
        st.header(f"📈 {get_text('cagr_method_title')}")
        st.markdown(get_text("cagr_description"))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(get_text("how_it_works"))
            st.markdown(get_text("cagr_how_it_works"))

        with col2:
            st.subheader(get_text("when_to_use"))
            st.markdown(get_text("cagr_when_to_use"))

        st.subheader(get_text("formula"))
        st.latex(
            r"CAGR = \left(\frac{Ending\_Value}{Beginning\_Value}\right)^{\frac{1}{years}} - 1"
        )
        st.markdown(get_text("cagr_formula_explanation"))

    with tab6:
        st.header(f"💳 {get_text('debt_method_title')}")
        st.markdown(get_text("debt_info_description"))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(get_text("how_it_works"))
            st.markdown(get_text("debt_how_it_works"))

        with col2:
            st.subheader(get_text("when_to_use"))
            st.markdown(get_text("debt_when_to_use"))

        st.subheader(get_text("formula"))
        st.latex(r"Debt\_Ratio_{Income} = \frac{Debt}{Net\_Income}")
        st.latex(r"Debt\_Ratio_{EBITDA} = \frac{Debt}{EBITDA}")
        st.latex(r"Debt\_Ratio_{CF} = \frac{Debt}{Operating\_Cash\_Flow}")
        st.markdown(get_text("debt_formula_explanation"))

    with tab7:
        st.header(f"💰 {get_text('profitability_method_title')}")
        st.markdown(get_text("profitability_info_description"))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(get_text("how_it_works"))
            st.markdown(get_text("profitability_how_it_works"))

        with col2:
            st.subheader(get_text("when_to_use"))
            st.markdown(get_text("profitability_when_to_use"))

        st.subheader(get_text("formula"))
        st.latex(r"ROE = \frac{Net\_Income}{Shareholders\_Equity}")
        st.latex(r"ROA = \frac{Net\_Income}{Total\_Assets}")
        st.latex(r"Gross\_Margin = \frac{Gross\_Profit}{Revenue}")
        st.latex(r"Operating\_Margin = \frac{Operating\_Income}{Revenue}")
        st.latex(r"Net\_Margin = \frac{Net\_Income}{Revenue}")
        st.latex(r"Asset\_Turnover = \frac{Revenue}{Total\_Assets}")
        st.markdown(get_text("profitability_formula_explanation"))

    with tab8:
        st.header(f"🌍 {get_text('suffix_guide_title')}")
        st.markdown(get_text("suffix_guide_intro"))

        # Wichtiger Hinweis für US-Aktien
        st.info(get_text("no_suffix_note"))
        st.markdown(f"**💡 {get_text('suffix_usage_tip')}**")

        # Suffix-Tabelle
        suffix_data = [
            ["🇺🇸 USA (NYSE, NASDAQ)", "*(none)*", "AAPL, MSFT", "USD"],
            ["🇨🇦 Canada - TSX", ".TO", "RY.TO", "CAD"],
            ["🇨🇦 Canada - TSX Venture", ".V", "GGD.V", "CAD"],
            ["🇨🇭 Switzerland - SIX", ".SW", "NESN.SW", "CHF"],
            ["🇩🇪 Germany - XETRA", ".F", "BMW.F", "EUR"],
            ["🇬🇧 United Kingdom - LSE", ".L", "HSBA.L", "GBP"],
            ["🇫🇷 France - Euronext Paris", ".PA", "OR.PA", "EUR"],
            ["🇳🇱 Netherlands - Euronext", ".AS", "UNA.AS", "EUR"],
            ["🇧🇪 Belgium - Euronext", ".BR", "ABI.BR", "EUR"],
            ["🇵🇹 Portugal - Euronext", ".LS", "EDP.LS", "EUR"],
            ["🇮🇹 Italy - Borsa Italiana", ".MI", "ENEL.MI", "EUR"],
            ["🇪🇸 Spain - Bolsa de Madrid", ".MC", "SAN.MC", "EUR"],
            ["🇳🇴 Norway - Oslo Stock Exchange", ".OL", "NHY.OL", "NOK"],
            ["🇩🇰 Denmark - Nasdaq Copenhagen", ".CO", "NOVO-B.CO", "DKK"],
            ["🇸🇪 Sweden - OMX Stockholm", ".ST", "VOLV-B.ST", "SEK"],
            ["🇫🇮 Finland - Helsinki", ".HE", "NOKIA.HE", "EUR"],
            ["🇭🇰 Hong Kong - HKEX", ".HK", "0005.HK", "HKD"],
            ["🇯🇵 Japan - Tokyo Stock Exchange", ".T", "7203.T", "JPY"],
            ["🇸🇬 Singapore - SGX", ".SI", "D05.SI", "SGD"],
            ["🇦🇺 Australia - ASX", ".AX", "BHP.AX", "AUD"],
            ["🇳🇿 New Zealand - NZX", ".NZ", "AIA.NZ", "NZD"],
            ["🇿🇦 South Africa - JSE", ".JO", "NPN.JO", "ZAR"],
            ["🇮🇳 India - BSE", ".BO", "TCS.BO", "INR"],
            ["🇮🇳 India - NSE", ".NS", "INFY.NS", "INR"],
            ["🇧🇷 Brazil - B3", ".SA", "PETR4.SA", "BRL"],
            ["🇲🇽 Mexico - BMV", ".MX", "AMXL.MX", "MXN"],
        ]

        # DataFrame erstellen und anzeigen
        import pandas as pd

        df = pd.DataFrame(
            suffix_data, columns=["Country / Exchange", "Suffix", "Example", "Currency"]
        )

        # Suchfunktion
        search_term = st.text_input("🔍 Search by country, suffix, or currency:")
        if search_term:
            mask = df.apply(
                lambda x: x.astype(str).str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            df_filtered = df[mask]
            st.dataframe(df_filtered, width="stretch", hide_index=True)
        else:
            st.dataframe(df, width="stretch", hide_index=True)

    with tab9:
        st.header(f"💡 {get_text('usage_guide_title')}")
        st.markdown(get_text("usage_guide_intro"))

        st.subheader(get_text("getting_started"))
        st.markdown(get_text("getting_started_steps"))

        st.subheader(get_text("tips_and_tricks"))
        st.markdown(get_text("tips_and_tricks_content"))
