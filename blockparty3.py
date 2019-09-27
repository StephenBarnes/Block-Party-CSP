#!/usr/bin/env python3

"""Implements a CP-SAT solver for Block Party 3 puzzle by Jane Street."""

from functools import reduce

from ortools.sat.python import cp_model


def BlockParty3(segments):
    """CP-SAT solver for Block Party 3 puzzle by Jane Street."""
    model = cp_model.CpModel()
    # TODO


class Board(object):
    def __init__(self, rows, cols, segments, given_values=None):
        self.rows = rows
        self.cols = cols
        self.segments = segments
        self.all_coords = reduce(lambda a,b: a | b, segments, set())
        if given_values is None:
            given_values = dict()
        self.given_values = given_values
        self.validate_unsolved()

    def validate_unsolved(self):
        """Check that given segments and values are valid."""
        # Check that all segments are within bounds
        for segment in self.segments:
            for block in segment:
                self.assert_in_bounds(block)
        # Check that every block appears in exactly one segment
        for y in range(self.rows):
            for x in range(self.cols):
                pos = (x, y)
                self.segment_of(pos)

    def segment_of(self, pos):
        """Return block containing the given pos."""
        self.assert_in_bounds(pos)
        segments_with_pos = [segment for segment in self.segments
                                if pos in segment]
        assert len(segments_with_pos) == 1, (pos, segments_with_pos)
        return segments_with_pos[0]

    def same_segment(self, *positions):
        assert len(positions) > 1
        segment = self.segment_of(positions[0])
        return all(pos in segment for pos in positions[1:])

    def assert_in_bounds(self, pos):
        """Assert given pos is within bounds."""
        assert 0 <= pos[0] < self.cols, pos
        assert 0 <= pos[1] < self.rows, pos

    def str_pos(self, pos):
        """
        Given coordinates of string representation, return one of:
        - None, if it's a border pos that should always be shown as ▓
        - (4, tuple of 4 neighboring board positions)
        - (1, a single board position)
        - (2, tuple of two board (x,y) positions neighboring it)
        """
        x, y = pos
        # The width-one border is always None
        if (x == 0) or (y == 0) or (x == self.cols * 2) or (y == self.rows * 2):
            return None

        xodd = bool(x % 2)
        yodd = bool(y % 2)
        # If x and y are even, it's a corner pos
        if not xodd and not yodd:
            botpos = (x // 2, (y - 1) // 2)
            toppos = (x // 2, (y + 1) // 2)
            leftpos = ((x - 1) // 2, y // 2)
            rightpos = ((x + 1) // 2, y // 2)
            return 4, (botpos, toppos, leftpos, rightpos)
        # If x and y are odd, it's a square center
        if xodd and yodd:
            return 1, (x // 2, y // 2)
        # If one is odd and one is even, it's a border between two squares
        if xodd and not yodd:
            botpos = (x // 2, (y - 1) // 2)
            toppos = (x // 2, (y + 1) // 2)
            return 2, (botpos, toppos)
        if not xodd and yodd:
            leftpos = ((x - 1) // 2, y // 2)
            rightpos = ((x + 1) // 2, y // 2)
            return 2, (leftpos, rightpos)

    def __str__(self):
        out = ""
        for y in range(self.rows * 2, -1, -1):
            for x in range(self.cols * 2 + 1):
                str_code = self.str_pos((x, y))
                if str_code is None:
                    out += "▓"
                else:
                    code, tup = str_code
                    if code == 1:
                        # tup is a pos
                        if tup in self.given_values:
                            out += str(self.given_values[tup])
                        else:
                            out += " "
                    elif code == 2:
                        pos1, pos2 = tup
                        if self.same_segment(pos1, pos2):
                            out += " "
                        else:
                            out += "▓"
                    elif code == 4:
                        if self.same_segment(*tup):
                            out += " "
                        else:
                            out += "▓"
                    else:
                        assert False
            out += "\n"
        return out


example_segments = (
        {(0,0),(0,1),(1,1),(1,2)},
        {(1,0),(2,0),(2,1)},
        {(3,0),(3,1),(4,0),(4,1)},
        {(0,2),(0,3),(0,4),(1,3)},
        {(3,2),(4,2),(4,3),(4,4)},
        {(2,2),(2,3),(3,3)},
        {(1,4),(2,4),(3,4)},
        )

print(Board(1, 1, ({(0,0)},)))
print(Board(2, 2, ({(0,0), (0,1), (1,0), (1,1)},)))
print(Board(5, 5, example_segments))
