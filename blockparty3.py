#!/usr/bin/env python3

"""Implements a CP-SAT solver for Block Party 3 puzzle by Jane Street."""

from functools import reduce

import constraint as C

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
        return ((0 <= pos[0] < self.cols)
                and (0 <= pos[1] < self.rows))

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

    def add_look_constraints(self, pos, problem):
        """
        Adds look-around constraint: if pos has value n, then the
        closest other value n looking horizontally/vertically must
        be exactly n spaces away.
        """
        x, y = pos

        for possible_val in range(1, len(self.segment_of(pos)) + 1):
            # Build constraints that say it's no nearer than `possible_val`
            unequal_positions = []
            for delta in range(1, possible_val):
                for other_pos in ((x, y + delta),
                                  (x, y - delta),
                                  (x + delta, y),
                                  (x - delta, y)):
                    if self.in_bounds(other_pos):
                        unequal_positions.append(other_pos)
            for unequal_pos in unequal_positions:
                print(f"{pos} != {possible_val} or {unequal_pos} != {possible_val}")
                # (1,3) != 2 or (1,4) != 2
                #   this constraint is indeed added, but the "solution" doesn't obey it!
                #
                problem.addConstraint(lambda thispos, other_pos: ((thispos != possible_val) or (other_pos != possible_val)),
                        (pos, unequal_pos))
            print(problem)
                    # NOTE there's something wrong here -- places 2 in 2 adjacent spots...

            # Build constraints that say a `possible_val` is exactly `possible_val` spaces away
            equal_positions = []
            for other_pos in ((x, y + possible_val),
                              (x, y - possible_val),
                              (x + possible_val, y),
                              (x - possible_val, y)):
                if self.in_bounds(other_pos):
                    equal_positions.append(other_pos)
            if not equal_positions:
                problem.addConstraint(lambda val: val != possible_val, (pos,))
            else:
                # It's just this part that causes issues; without this it works fine:
                if False:
                    problem.addConstraint(
                            (lambda atpos, *rest:
                                    ((atpos != possible_val)
                                    or any([other == possible_val for other in rest]))),
                            (pos, *equal_positions))



    def solve(self):
        """Fills out self.values using python-constraint's CSP solver."""
        #problem = C.Problem(C.MinConflictsSolver(100000))
        #problem = C.Problem(C.BacktrackingSolver())
        #problem = C.Problem(C.RecursiveBacktrackingSolver())
        problem = C.Problem()
        # Add variables
        for y in range(self.rows):
            for x in range(self.cols):
                if (x, y) in self.given_values:
                    problem.addVariable((x, y), [self.given_values[x, y]])
                else:
                    problem.addVariable((x, y), range(1, len(self.segment_of((x, y))) + 1))
        # Add constraints: each segment must have all values different
        for segment in self.segments:
            for pos1 in segment:
                for pos2 in segment:
                    if pos1 < pos2:
                        problem.addConstraint(lambda p1, p2: p1 != p2,
                                (pos1, pos2))
        # Add look-around constraints
        for y in range(self.rows):
            for x in range(self.cols):
                self.add_look_constraints((x, y), problem)
        # Solve the CSP
        solution = problem.getSolution()
        assert solution is not None
        #print(problem.getSolutions())
        self.solved_values = solution

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
board = Board(5, 5, example_segments)#, {(1,1):3})
#board = Board(2, 2, ({(0, 0)}, {(0, 1)}, {(1, 0)}, {(1, 1)}))
#board = Board(5, 5, example_segments)
print(board)
board.solve()
print(board)
#print(board.keycode())

