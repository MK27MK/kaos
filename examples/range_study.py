from research import Study, Hypothesis  # , RangeStudy?
from data import Universe, Instrument

# come gestire i vari contratti? dare a Instrument una timeline definita
# tramite rollover effettuati in anticipo? Io preferirei dargli tutti
# i contratti e farglieli gestire.
data = ...


specifications: InstrumentSpecs = None
E6 = Instrument(specifications, data)
intruments: list[Instrument] = [E6]
universe: Universe = Universe(instruments)
# hypothesis example:
#
# possible parameters: categories,
hypothesis: Hypothesis = Hypothesis(...)

study = Study(universe, hypothesis)
