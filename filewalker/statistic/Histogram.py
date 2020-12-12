####################################################################################################
#
# filewalker — ...
# Copyright (C) 2020 Fabrice Salvaire
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
####################################################################################################

####################################################################################################

import math

import numpy as np

from IntervalArithmetic import Interval

from .Binning import NDMixin, Binning1D, BinningND

####################################################################################################

class DataSetMoment:

    ##############################################

    def __init__(self, number_of_entries=0, sum_x=0, sum_x2=0, sum_x3=0, sum_x4=0):

        self.number_of_entries = number_of_entries
        self.sum_x = sum_x
        self.sum_x2 = sum_x2

        self.sum_x3 = sum_x3
        self.sum_x4 = sum_x4 # unused

    ##############################################

    def clone(self):
        return self.__class__(
            self.number_of_entries,
            self.sum_x, self.sum_x2, self.sum_x3, self.sum_x4,
        )

    ##############################################

    def to_json(self):
        return {
            'number_of_entries': self.number_of_entries,
            'sum_x': self.sum_x,
            'sum_x2': self.sum_x2,
            'sum_x3': self.sum_x3,
            'sum_x4': self.sum_x4,
        }

    ##############################################

    @staticmethod
    def from_json(data):
        return DataSetMoment(**data)

    ##############################################

    def fill(self, x):
        self.number_of_entries += 1
        self.sum_x += x
        self.sum_x2 += x**2
        self.sum_x3 += x**3
        self.sum_x4 += x**4

    ##############################################

    def __iadd__(self, obj):
        self.number_of_entries += obj.number_of_entries
        self.sum_x += obj.sum_x
        self.sum_x2 += obj.sum_x2
        self.sum_x3 += obj.sum_x3
        self.sum_x4 += obj.sum_x4
        return self

    ##############################################

    @property
    def mean(self):
        return self.sum_x / self.number_of_entries

    ##############################################

    @property
    def biased_variance(self):
        return self.sum_x2 / self.number_of_entries - self.mean**2

    ##############################################

    @property
    def unbiased_variance(self):
        return self.number_of_entries / (self.number_of_entries -1) * self.biased_variance

    ##############################################

    @property
    def biased_standard_deviation(self):
        return math.sqrt(self.biased_variance)

    ##############################################

    @property
    def standard_deviation(self):
        return math.sqrt(self.unbiased_variance)

    ##############################################

    @property
    def skew(self):
        return ((self.sum_x3 / self.number_of_entries - 3*self.mean*self.biased_variance - self.mean**3)
                / (self.biased_variance*self.biased_standard_deviation))

    ##############################################

    @property
    def kurtosis(self):
        # Need an expansion in terms of sum_x**i
        return NotImplementedError

####################################################################################################

class DataSetMomentND(NDMixin):

    ##############################################

    def __init__(self, dimension):
        NDMixin.__init__(self, [DataSetMoment() for i in xrange(dimension)])

    ##############################################

    def fill(self, *args):
        pass
        # Fixme:
        # for data_set_moment, x in zip(self, args):
        #     data_set_moment.fill(x)

####################################################################################################

class WeightedDataSetMoment:

    ##############################################

    def __init__(self):
        self.sum_weight = 0
        self.sum_weight2 = 0
        self.sum_weight_x = 0
        self.sum_weight_x2 = 0
        self.sum_weight_x3 = 0
        self.sum_weight_x4 = 0

    ##############################################

    def fill(self, x, weight=1.):
        self.sum_weight += weight
        self.sum_weight2 += weight**2
        weight_x = weight * x
        self.sum_weight_x += weight_x
        self.sum_weight_x2 += weight_x**2
        self.sum_weight_x3 += weight_x**3
        self.sum_weight_x4 += weight_x**4

    ##############################################

    @property
    def number_of_effective_entries(self):
        return self.sum_weight**2 / self.sum_weight2

    ##############################################

    @property
    def mean(self):
        return self.sum_weight_x / self.number_of_effective_entries

####################################################################################################

class Histogram:

    ##############################################

    def __init__(self, binning):

        # Fixme: direct mode

        if isinstance(binning, Binning1D):
            self._binning = binning
        else:
            raise ValueError

        self._make_array(self._binning.array_size)
        self.data_set_moment = DataSetMoment()

        self.clear_feature()

    ##############################################

    def _make_array(self, array_size):
        self._accumulator = np.zeros(array_size)
        self._sum_weight_square = np.zeros(array_size)

    ##############################################

    def clone(self):
        histogram = self.__class__(self._binning.clone())
        histogram += self
        return histogram

    ##############################################

    def to_json(self):
        return {
            'binning': self._binning.to_json(),
            'data_set_moment': self.data_set_moment.to_json(),
            'accumulator': list(self._accumulator),
            'sum_weight_square': list(self._sum_weight_square),
        }

    ##############################################

    @staticmethod
    def from_json(data):
        binning = Binning1D.from_json(data['binning'])
        histogram = Histogram(binning)
        histogram.data_set_moment += DataSetMoment.from_json(data['data_set_moment'])
        histogram._accumulator[...] = data['accumulator']
        histogram._sum_weight_square[...] = data['sum_weight_square']

        return histogram

    ##############################################

    def rebin(self, factor=2):

        # binning = self.binning
        # print binning.interval, binning.number_of_bins, binning.bin_width, self._accumulator.shape

        histogram = self.__class__(Binning1D(self._binning.interval, bin_width=self._binning.bin_width*factor))
        binning = histogram.binning
        # print binning.interval, binning.number_of_bins, binning.bin_width

        # copy under/over flow bins
        for i in (0, -1):
            histogram._accumulator[i] = self._accumulator[i]
            histogram._sum_weight_square[i] = self._sum_weight_square[i]

        start = 1
        for i in binning.bin_iterator():
            stop = min(start + factor, self.binning.number_of_bins)
            # print i, start, stop
            histogram._accumulator[i] = np.sum(self._accumulator[start:stop])
            histogram._sum_weight_square[i] = np.sum(self._sum_weight_square[start:stop])
            start = stop

        # Fixme: merge last bin when the rebin factor is not a multiple
        over_flow_bin = self.binning.over_flow_bin
        if stop < over_flow_bin:
            # print "Merge last bin"
            histogram._accumulator[i] += np.sum(self._accumulator[stop:over_flow_bin])
            histogram._sum_weight_square[i] += np.sum(self._sum_weight_square[stop:over_flow_bin])

        histogram.data_set_moment += self.data_set_moment

        return histogram

    ##############################################

    def clear(self, value=.0):
        self._accumulator[:] = value
        self._sum_weight_square[:] = value**2
        self.data_set_moment = DataSetMoment()
        self.clear_feature()

    ##############################################

    def clear_feature(self):
        self._errors = None
        self._integral = None
        self._mean = None
        self._biased_variance = None

    ##############################################

    @property
    def binning(self):
        return self._binning

    @property
    def accumulator(self):
        return self._accumulator

    @property
    def binning_accumulator(self):
        return self._accumulator[1:-1]

    @property
    def x_values(self):
        return self._binning.bin_centers

    @property
    def min(self):
        return float(np.min(self._accumulator))

    @property
    def max(self):
        return float(np.max(self._accumulator))

    ##############################################

    def is_consistent_with(self, obj):
        return self._binning == obj._binning

    ##############################################

    def __iadd__(self, obj):

        if isinstance(obj, Histogram):
            if self.is_consistent_with(obj):
                self._accumulator += obj._accumulator
                self._sum_weight_square += obj._sum_weight_square
                self.data_set_moment += obj.data_set_moment
                self.clear_feature()
            else:
                raise ValueError
        else:
            float_obj = float(obj)
            self._accumulator += float_obj
            self._sum_weight_square += float_obj**2
            # self.data_set_moment += ...
        self.clear_feature()

        return self

    ##############################################

    def __isub__(self, obj):

        if isinstance(obj, Histogram):
            if self.is_consistent_with(obj):
                self._accumulator -= obj._accumulator
                self._sum_weight_square -= obj._sum_weight_square
                self.data_set_moment -= obj.data_set_moment
                self.clear_feature()
            else:
                raise ValueError
        else:
            float_obj = float(obj)
            self._accumulator -= float_obj
            self._sum_weight_square -= float_obj**2
            # self.data_set_moment -= ...
        self.clear_feature()

        return self

    ##############################################

    def __imul__(self, obj):

        # Fixme: data_set_moment

        if isinstance(obj, Histogram):
            if self.is_consistent_with(obj):
                self._accumulator *= obj._accumulator
                self._sum_weight_square[...] = 0
                # self._sum_weight_square *= obj._sum_weight_square
                # self.data_set_moment *= obj.data_set_moment # Fixme: Right ???
            else:
                raise ValueError
        else:
            float_obj = float(obj)
            self._accumulator *= float_obj
            self._sum_weight_square *= float_obj**2
            # self.data_set_moment *= float_obj
        self.clear_feature()

        return self

    ##############################################

    def __truediv__(self, obj):

        # Fixme: data_set_moment

        if isinstance(obj, Histogram):
            if self.is_consistent_with(obj):
                numerator = self._accumulator
                denominator = obj._accumulator
                efficiency = np.nan_to_num(numerator / denominator)
                self._accumulator = efficiency
                self._sum_weight_square[...] = self._binomial_variance_unweighted(efficiency, denominator)
                # self.data_set_moment /= obj.data_set_moment # Fixme: Right ???
            else:
                raise ValueError
        else:
            float_obj = float(obj)
            self._accumulator /= float_obj
            self._sum_weight_square /= float_obj**2
            # self.data_set_moment /= float_obj
        self.clear_feature()

        return self

    ##############################################

    @staticmethod
    def _binomial_variance_unweighted(efficiency, denominator):

        # Formulae for unweighted case
        return np.abs((efficiency * (1 - efficiency))/ denominator)

        # Formulae for weighted case
        # w = b1/b2
        # abs( ( (1 - 2*w)*e1**2 + (w*e2)**2 ) / b2**2 )

        # d2 = denominator**2
        # en = np.sqrt(numerator)
        # en2 = en**2 # Fixme: check
        # ed = np.sqrt(denominator)
        # eed = efficiency * ed
        # ee = np.abs( ( (1 - 2*efficiency)*en2 + eed**2 ) / d2 )
        # return ee

    ##############################################

    def __add__(obj1, obj2):
        obj = obj1.clone()
        obj += obj2
        return obj

    ##############################################

    def __sub__(obj1, obj2):
        obj = obj1.clone()
        obj -= obj2
        return obj

    ##############################################

    def __mul__(obj1, obj2):
        obj = obj1.clone()
        obj *= obj2
        return obj

    ##############################################

    def __div__(obj1, obj2):
        obj = obj1.clone()
        obj /= obj2
        return obj

    ##############################################

    def normalise(self):
        histogram = self.clone()
        histogram /= histogram.integral
        histogram.clear_feature()
        return histogram

    ##############################################

    def cumulative(self, normalise=True):
        histogram = self.clone()
        histogram.clear_feature()
        histogram._accumulator = np.cumsum(histogram._accumulator) # overflow ?
        histogram._sum_weight_square = np.cumsum(histogram._sum_weight_square)
        if normalise:
            histogram.normalise()
        return histogram

    ##############################################

    def inverse_cumulative(self, normalise=True):

        histogram = self.clone()
        denominator = histogram.integral
        if normalise:
            histogram._accumulator /= denominator
            sup = 1
        else:
            sup = histogram.integral
        inverse_cumulative = sup - np.cumsum(histogram._accumulator) # overflow ?
        histogram._accumulator[1] = sup
        histogram._accumulator[2:-1] = inverse_cumulative[1:-2]
        # Fixme: check, should be computed in div
        histogram._sum_weight_square[...] = self._binomial_variance_unweighted(histogram._accumulator, denominator)
        histogram.clear_feature()
        return histogram

    ##############################################

    def efficiency(self):
        # eff = Sum x>t / integral
        return self.inverse_cumulative()

    ##############################################

    def purity(self, denominator):
        # eff = Sum N x>t / Sum D x>t
        numerator = self.inverse_cumulative(normalise=False)
        denominator = denominator.inverse_cumulative(normalise=False)
        purity = numerator / denominator
        return purity

    ##############################################

    def fill(self, *values, **kwargs):

        weight = kwargs.get('weight', 1.)

        if weight < 0:
            raise ValueError

        i = self._binning.find_bin(*values)
        self._accumulator[i] += weight
        # if weight == 1.: weight_square = 1.
        self._sum_weight_square[i] += weight**2
        self.data_set_moment.fill(*values)
        self.clear_feature()

    ##############################################

    def compute_errors(self):
        if self._errors is None:
            self._errors = np.sqrt(self._sum_weight_square)

    ##############################################

    def get_bin_error(self, i):
        self.compute_errors()
        return self._errors[i]

    ##############################################

    @property
    def min(self):
        return min(self._accumulator) # - self._errors
    inf = min

    ##############################################

    @property
    def max(self):
        return max(self._accumulator) # + self._errors
    sup = max

    ##############################################

    @property
    def integral(self):
        if self._integral is None:
            self._integral = self._accumulator.sum()
        return self._integral

    ##############################################

    @property
    def number_of_effective_entries(self):
        return self.integral**2 / self._sum_weight_square.sum()

    ##############################################

    @property
    def mean(self):
        if self._mean is None:
            # if weighted: / self.number_of_effective_entries
            self._mean = np.sum(self.binning_accumulator * self.x_values) / self.integral
        return self._mean

    ##############################################

    @property
    def biased_variance(self):
        if self._biased_variance is None:
            self._biased_variance = np.sum(self.binning_accumulator * self.x_values**2) / self.integral - self.mean**2
        return self._biased_variance

    ##############################################

    @property
    def unbiased_variance(self):
        return self.integral / (self.integral -1) * self.biased_variance

    ##############################################

    @property
    def biased_standard_deviation(self):
        return math.sqrt(self.biased_variance)

    ##############################################

    @property
    def standard_deviation(self):
        return math.sqrt(self.unbiased_variance)

    ##############################################

    @property
    def skew(self):
        # self.biased_variance * self.biased_standard_deviation
        return (np.sum(self.binning_accumulator * (self.x_values - self.mean)**3)
                / (self.biased_standard_deviation**3 * self.integral))

    ##############################################

    @property
    def kurtosis(self):
        return (np.sum(self.binning_accumulator * (self.x_values - self.mean)**4)
                / (self.biased_variance**2 * self.integral)
                -3)

    ##############################################

    def to_graph(self):

        self.compute_errors()

        binning = self._binning
        bin_slice = binning.bin_slice()

        x_values = self.x_values

        y_values = np.copy(self._accumulator[bin_slice])
        y_errors = np.copy(self._errors[bin_slice])

        x_errors = np.empty(x_values.shape)
        x_errors[:] = .5*binning.bin_width

        return x_values, y_values, x_errors, y_errors

   ###############################################

    def __str__(self):

        binning = self._binning

        string_format = """
Histogram 1D
  interval: %s
  number of bins: %u
  bin width: %g
"""

        text = string_format % (str(binning._interval), binning._number_of_bins, binning._bin_width)
        for i in binning.bin_iterator(xflow=True):
            text += '%3u %s = %g +- %g\n' % (i,
                                             str(binning.bin_interval(i)),
                                             self._accumulator[i],
                                             self.get_bin_error(i),
                                             )

        return text

   ###############################################

    def find_non_zero_bin_range(self):

        inf = 0
        while self._accumulator[inf] == 0:
            inf += 1

        sup = len(self._accumulator) -1
        while self._accumulator[sup] == 0:
            sup -= 1

        return Interval(inf, sup)

   ###############################################

    def non_zero_bin_range_histogram(self):

        bin_range = self.find_non_zero_bin_range()
        binning = self._binning.sub_binning(self._binning.sub_interval(bin_range))
        histogram = self.__class__(binning)
        src_slice = slice(bin_range.inf, bin_range.sup +1)
        dst_slice = slice(binning.first_bin, binning.over_flow_bin)
        histogram._accumulator[dst_slice] = self._accumulator[src_slice]
        histogram._sum_weight_square[dst_slice] = self._sum_weight_square[src_slice]
        histogram._errors[dst_slice] = self._errors[src_slice]

        return histogram

####################################################################################################

class Histogram2D(Histogram):

    ##############################################

    def __init__(self, binning):

        if isinstance(binning, BinningND) and binning.dimension == 2:
            self._binning = binning
        else:
            raise ValueError

        array_size = [binning.array_size for binning in self._binning]
        self._make_array(array_size)
        self.data_set_moment = DataSetMomentND(dimension=2)

        # self.clear_feature()

    ##############################################

    def box_plot(self, axes=None):

        """Also called Hinton diagram"""

        import matplotlib.pyplot as plt

        # Return the current axes, creating one if necessary
        axes = axes if axes is not None else plt.gca()

        if np.min(self._accumulator) < 0:
            raise ValueError("Bin contents must be positive")

        # Set bin content to a normalised square area
        accumulator_view = self._accumulator[1:-1,1:-1]
        accumulator = np.sqrt(accumulator_view / np.max(accumulator_view))
        # Add margin
        accumulator *= .90

        for (x, y), size in np.ndenumerate(accumulator):
            rect = plt.Rectangle([x - size / 2, y - size / 2], size, size,
                                 edgecolor='black', facecolor='white')
            axes.add_patch(rect)

        axes.set_aspect('equal', 'box')
        x_size, y_size = accumulator_view.shape
        axes.set_xlim(-.5, x_size)
        axes.set_ylim(-.5, y_size)
        labels = [str(x) for x in self._binning.x.bin_centers]
        plt.xticks(np.arange(x_size) +.5, labels, rotation='vertical')
        labels = [str(x) for x in self._binning.y.bin_centers]
        plt.yticks(np.arange(y_size) +.5, labels)
