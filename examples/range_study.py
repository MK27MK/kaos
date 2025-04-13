from research import Study, Hypothesis  # , RangeStudy?
from ... import Universe

universe: Universe = Universe()
# hypothesis example:
#
# possible parameters: categories,
hypothesis: Hypothesis = Hypothesis(...)

study = Study(universe, hypothesis)
