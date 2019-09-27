#!/usr/bin/env python3

"""Implements a CP-SAT solver for Block Party 3 puzzle by Jane Street."""

from functools import reduce

from ortools.sat.python import cp_model
#import constraint as C

WALL_CHAR = "▓"



class Board(object):
    def __init__(self, rows, cols, segments, given_values=None):
        self.rows = rows
        self.cols = cols
        self.segments = segments
        self.all_coords = reduce(lambda a,b: a | b, segments, set())
        if given_values is None:
            given_values = dict()
        self.given_values = given_values
        self.solved_values = None
        self.validate_unsolved()

    def validate_unsolved(self):
        """Check that given segments and values are valid."""
        # Check that all segments are within bounds
        for segment in self.segments:
            for block in segment:
                assert self.in_bounds(block)
        # Check that every block appears in exactly one segment
        for y in range(self.rows):
            for x in range(self.cols):
                pos = (x, y)
                self.segment_of(pos)

    def segment_of(self, pos):
        """Return block containing the given pos."""
        assert self.in_bounds(pos)
        segments_with_pos = [segment for segment in self.segments
                                if pos in segment]
        assert len(segments_with_pos) == 1, (pos, segments_with_pos)
        return segments_with_pos[0]

    def same_segment(self, *positions):
        """Return whether positions are in the same segment."""
        assert len(positions) > 1
        segment = self.segment_of(positions[0])
        return all(pos in segment for pos in positions[1:])

    def in_bounds(self, pos):
        """Return whether given pos is within bounds."""
        return (0 <= pos[0] < self.cols, pos
                and 0 <= pos[1] < self.rows, pos)

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

    def value_at(self, pos):
        """
        Return value at given pos, either a given value or a value found
        by the solver, if it's been run yet; else None.
        """
        if self.given_values is not None:
            if pos in self.given_values:
                return self.given_values[pos]
        if self.solved_values is not None:
            return self.solved_values[pos]
        return None

    def __str__(self):
        out = ""
        for y in range(self.rows * 2, -1, -1):
            for x in range(self.cols * 2 + 1):
                str_code = self.str_pos((x, y))
                if str_code is None:
                    out +=  WALL_CHAR
                else:
                    code, tup = str_code
                    if code == 1:
                        # tup is a pos
                        val = self.value_at(tup)
                        if val is None:
                            out += " "
                        else:
                            out += str(val)
                    elif code == 2:
                        pos1, pos2 = tup
                        if self.same_segment(pos1, pos2):
                            out += " "
                        else:
                            out += WALL_CHAR
                    elif code == 4:
                        if self.same_segment(*tup):
                            out += " "
                        else:
                            out += WALL_CHAR
                    else:
                        assert False
            out += "\n"
        return out

    def add_look_constraints(self, pos, model, nums):
        """
        Adds look-around constraint: if pos has value n, then the
        closest other value n looking horizontally/vertically must
        be exactly n spaces away.
        """
        x, y = pos
        for possible_val in range(1, len(self.segment_of((x, y))) + 1):
            # Build constraints that say it's no nearer than `possible_val`
            unequal_parts = []
            for delta in range(1, possible_val):
                if y + delta < self.rows:
                    unequal_parts.append(nums[x, y + delta] != possible_val)
                if y - delta >= 0:
                    unequal_parts.append(nums[x, y - delta] != possible_val)
                if x + delta < self.cols:
                    unequal_parts.append(nums[x + delta, y] != possible_val)
                if x - delta >= 0:
                    unequal_parts.append(nums[x - delta, y] != possible_val)
            inequality_constraint = reduce(lambda x, y: x and y, unequal_parts, True)

            # Build constraints that say a `possible_val` is exactly `possible_val` spaces away
            equal_parts = []
            if y + possible_val < self.rows:
                equal_parts.append(nums[x, y + possible_val] == possible_val)
            if y - possible_val >= 0:
                equal_parts.append(nums[x, y - possible_val] == possible_val)
            if x + possible_val < self.cols:
                equal_parts.append(nums[x + possible_val, y] == possible_val)
            if x - possible_val >= 0:
                equal_parts.append(nums[x - possible_val, y] == possible_val)
            equality_constraint = reduce(lambda x, y: x or y, equal_parts, False)

            total_constraint = inequality_constraint and equality_constraint
            model.Add(total_constraint).OnlyEnforceIf(nums[pos] == possible_val)


    def solve(self):
        """Fills out self.values using ormtools's CSP-SAT solver."""
        model = cp_model.CpModel()
        # Add variables
        nums = dict()
        for y in range(self.rows):
            for x in range(self.cols):
                nums[x, y] = model.NewIntVar(1, len(self.segment_of((x, y))), str((x, y)))
        # Add constraints: each segment must have all values different
        for segment in self.segments:
            model.AddAllDifferent(nums[pos] for pos in segment)
        # Add given-value constraints
        for k, v in self.given_values.items():
            model.Add(nums[k] == v)
        # Add look-around constraints
        for y in range(self.rows):
            for x in range(self.cols):
                self.add_look_constraints((x, y), model, nums)
        # TODO
        # Solve the CSP
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status == cp_model.FEASIBLE, status
        self.solved_values = dict()
        for y in range(self.rows):
            for x in range(self.cols):
                self.solved_values[x, y] = solver.Value(nums[x, y])




    def keycode(self):
        """
        After solving board, prints out code.
        Code is sum of largest horizontal number in each segment.
        """
        raise NotImplementedError() # TODO
        


example_segments = (
        {(0,0),(0,1),(1,1),(1,2)},
        {(1,0),(2,0),(2,1)},
        {(3,0),(3,1),(4,0),(4,1)},
        {(0,2),(0,3),(0,4),(1,3)},
        {(3,2),(4,2),(4,3),(4,4)},
        {(2,2),(2,3),(3,3)},
        {(1,4),(2,4),(3,4)},
        )

#print(Board(1, 1, ({(0,0)},)))
#print(Board(2, 2, ({(0,0), (0,1), (1,0), (1,1)},)))
board = Board(5, 5, example_segments, {(1,1):1})
print(board)
board.solve()
print(board)
#print(board.keycode())

