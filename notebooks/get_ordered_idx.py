from typing import Tuple

import numpy as np


def _get_ordered_idx(idx: dict) -> Tuple[list, list]:
    """Takes a list of peaks and troughs and removes
       out of order elements. Regardless of which occurs first,
       a peak or a trough, a peak must be followed by a trough
       and vice versa.

    Algorithm (if peaks start first)
    ---------
    - Loop through values starting with first peak
    - Is peak before valley?
        YES -> Is next peak after valley?
            YES -> Append peak and valley. Get next peak and valley.
            NO  -> Get next peak.
        NO  -> Get next valley.

    Args:
        peaks (list): Signal peaks.
        troughs (list): Signal troughs.

    Returns:
        first_repaired (list): Input with out of order items removed.
        second_repaired (list): Input with out of order items removed.

        Items are always returned with peaks idx as first tuple item.
    """
    order_lists = lambda x, y : (x, y, 0, 1) if x[0] < y[0] else (y, x, 1, 0)

    # Configure algorithm to start with lowest index.
    peaks, troughs = idx['peaks'], idx['troughs']

    try:
        first, second, flag1, flag2 = order_lists(peaks, troughs)
    except IndexError:
        return dict(peaks=np.array([]), troughs=np.array([]))

    result = dict(first=[], second=[])
    i, j = 0, 0
    for _ in enumerate(first):
        try:
            poi_1, poi_2 = first[i], second[j]
            if poi_1 < poi_2:  # first point of interest is before second
                poi_3 = first[i + 1]
                if poi_2 < poi_3:  # second point of interest is before third
                    result['first'].append(poi_1)
                    result['second'].append(poi_2)
                    i += 1; j += 1
                else:
                    i += 1
            else:
                j += 1
        except IndexError: # always thrown in last iteration
            result['first'].append(poi_1)
            result['second'].append(poi_2)

    # remove duplicates and return as peaks, troughs
    result['first'] = sorted(list(set(result['first'])))
    result['second'] = sorted(list(set(result['second'])))
    result = [result['first'], result['second']]
    return dict(peaks=np.array(result[flag1]), troughs=np.array(result[flag2]))
