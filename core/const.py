from core.instrument import Instrument

##########
# KRAKEN #
##########
KRAKEN_NAME_TO_INSTRUMENTS = {
    'btc_usd_perp': Instrument(name='btc_usd_perp', instrument_id='PI_XBTUSD', tick_size=0.5, size_unit=1),
    'eth_usd_perp': Instrument(name='eth_usd_perp', instrument_id='PI_ETHUSD', tick_size=0.05, size_unit=1),
    'ltc_usd_perp': Instrument(name='ltc_usd_perp', instrument_id='PI_LTCUSD', tick_size=0.01, size_unit=1),
    'xrp_usd_perp': Instrument(name='xrp_usd_perp', instrument_id='PI_XRPUSD', tick_size=0.0001, size_unit=1),
    'btc_usd': Instrument(name='btc_usd', instrument_id='XBT/USD', tick_size=0.1, size_unit=0.00000001),
    'eth_usd': Instrument(name='eth_usd', instrument_id='ETH/USD', tick_size=0.01, size_unit=0.0000001),
    'ltc_usd': Instrument(name='ltc_usd', instrument_id='LTC/USD', tick_size=0.01, size_unit=0.0000001),
    'xrp_usd': Instrument(name='xrp_usd', instrument_id='XRP/USD', tick_size=0.00001, size_unit=0.0001)
}

KRAKEN_TICKER_TO_INSTRUMENTS = {v.instrument_id: v for v in KRAKEN_NAME_TO_INSTRUMENTS.values()}

# TODO: ADD following instruments (complement tick_size + size_unit)
# 'ada_usd_spot': Instrument(name='ada_usd_spot', instrument_id='ADAUSD'),
# 'atom_usd_spot': Instrument(name='atom_usd_spot', instrument_id='ATOMUSD'),
# 'bch_usd_spot': Instrument(name='bch_usd_spot', instrument_id='BCHUSD'),
# 'btc_usd_spot': Instrument(name='btc_usd_spot', instrument_id='XXBTZUSD'),
# 'dot_usd_spot': Instrument(name='dot_usd_spot', instrument_id='DOTUSD'),
# 'eos_usd_spot': Instrument(name='eos_usd_spot', instrument_id='EOSUSD'),
# 'eth_usd_spot': Instrument(name='eth_usd_spot', instrument_id='XETHZUSD'),
# 'link_usd_spot': Instrument(name='link_usd_spot', instrument_id='LINKUSD'),
# 'ltc_usd_spot': Instrument(name='ltc_usd_spot', instrument_id='XLTCZUSD'),
# 'xlm_usd_spot': Instrument(name='xlm_usd_spot', instrument_id='XXLMZUSD'),
# 'xrp_usd_spot': Instrument(name='xrp_usd_spot', instrument_id='XXRPZUSD')

#######
# FTX #
#######
FTX_NAME_TO_INSTRUMENTS = {
    'btc_usd_perp': Instrument(name='btc_usd_perp', instrument_id='BTC-PERP', tick_size=1, size_unit=0.0001),
    'btc_usd_spot': Instrument(name='btc_usd_spot', instrument_id='BTC/USD', tick_size=1, size_unit=0.0001),
    'eth_usd_perp': Instrument(name='eth_usd_perp', instrument_id='ETH-PERP', tick_size=0.01, size_unit=0.001),
    'eth_usd_spot': Instrument(name='eth_usd_spot', instrument_id='ETH/USD', tick_size=0.1, size_unit=0.001),
    'ltc_usd_perp': Instrument(name='ltc_usd_perp', instrument_id='LTC-PERP', tick_size=0.01, size_unit=0.01),
    'ltc_usd_spot': Instrument(name='ltc_usd_spot', instrument_id='LTC/USD', tick_size=0.005, size_unit=0.01),
    'xrp_usd_perp': Instrument(name='xrp_usd_perp', instrument_id='XRP-PERP', tick_size=0.000025, size_unit=1),
    'xrp_usd_spot': Instrument(name='xrp_usd_spot', instrument_id='XRP/USD', tick_size=0.000025, size_unit=1)
}

FTX_TICKER_TO_INSTRUMENTS = {v.instrument_id: v for v in FTX_NAME_TO_INSTRUMENTS.values()}

# TODO: ADD following instruments (complement tick_size + size_unit)
# 'ada_usd_perp': Instrument(name='ada_usd_perp', instrument_id='ADA-PERP'),
# 'algo_usd_perp': Instrument(name='algo_usd_perp', instrument_id='ALGO-PERP'),
# 'atom_usd_perp': Instrument(name='atom_usd_perp', instrument_id='ATOM-PERP'),
# 'bch_usd_perp': Instrument(name='bch_usd_perp', instrument_id='BCH-PERP'),
# 'bnb_usd_perp': Instrument(name='bnb_usd_perp', instrument_id='BNB-PERP'),
# 'comp_usd_perp': Instrument(name='comp_usd_perp', instrument_id='COMP-PERP'),
# 'dot_usd_perp': Instrument(name='dot_usd_perp', instrument_id='DOT-PERP'),
# 'eos_usd_perp': Instrument(name='eos_usd_perp', instrument_id='EOS-PERP'),
# 'ftt_usd_perp': Instrument(name='ftt_usd_perp', instrument_id='FTT-PERP'),
# 'link_usd_perp': Instrument(name='link_usd_perp', instrument_id='LINK-PERP'),
# 'snx_usd_perp': Instrument(name='snx_usd_perp', instrument_id='SNX-PERP'),
# 'uni_usd_perp': Instrument(name='uni_usd_perp', instrument_id='UNI-PERP'),
# 'xlm_usd_perp': Instrument(name='xlm_usd_perp', instrument_id='XLM-PERP'),
# 'yfi_usd_perp': Instrument(name='yfi_usd_perp', instrument_id='YFI-PERP')
