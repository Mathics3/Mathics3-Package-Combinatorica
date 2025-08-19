# -*- coding: utf-8 -*-

import os.path as osp
from test.helper import check_evaluation, evaluate, reset_session

import pytest

# This variable is set to initialize the module just once,
# and just before running the tests.
_initialized: bool = False

combinatorica_file = osp.normpath(
    osp.join(osp.dirname(__file__),
             "..", "Combinatorica",
             "CombinatoricaV201.m")
)


@pytest.fixture(autouse=True)
def reset_and_load_package():
    global _initialized
    if not _initialized:
        reset_session()
        evaluate(
            f"""
        Get["{combinatorica_file}"]
        """
        )
        _initialized = True
    yield


# A number of examples from:
#  * Implementing Discrete Mathematics by Steven Skiena and
#  * Computation Discrete Mathematics by Sriram Pemmaraju and Steven Skiena.

# Page numbers below come from this book.
# Some tests have been altered to speed them up, or to make the intent
# more clear in a test.


def test_permutations_and_subsets_1_1_1():
    for str_expr, str_expected, message in (
        (
            "Permutations[3]",
            "{{1, 2, 3}, {1, 3, 2}, {2, 1, 3}, {2, 3, 1}, "
            "{3, 1, 2}, {3, 2, 1}}",
            "Permutations; 1.1.1 Page 3",
        ),
        (
            "Permute[{A, B, C, D}, Permutations[3]]",
            "{{A, B, C}, {A, C, B}, {B, A, C}, {B, C, A}, {C, A, B}, "
            "{C, B, A}}",
            "Permute operator; 1.1.1 Page 3",
        ),
        (
            "Permute[{5, 2, 4, 3, 1}, InversePermutation[{5, 2, 4, 3, 1}]]",
            "{1, 2, 3, 4, 5}",
            "Inverse permutation, 1.1.1 Page 3",
        ),
        (
            "MinimumChangePermutations[{a, b, c}]",
            "{{a, b, c}, {b, a, c}, {c, a, b}, {a, c, b}, "
            "{b, c, a}, {c, b, a}}",
            "Minimum-change permutation, 1.1.1, Page 3",
        ),
        (
            "RankPermutation[{8, 9, 7, 1, 6, 4, 5, 3, 2}]",
            "321953",
            "ranking permutation function; 1.1.1, Page 3",
        ),
        (
            "UnrankPermutation[321953, 9]",
            "{8, 9, 7, 1, 6, 4, 5, 3, 2}",
            "Unrank permutation, 1.1.1, Page 4",
        ),
        (
            "UnrankPermutation[0, 9]",
            "{1, 2, 3, 4, 5, 6, 7, 8, 9}",
            "additional test 1 - not part of text]",
        ),
        (
            "UnrankPermutation[1, 9]",
            "{1, 2, 3, 4, 5, 6, 7, 9, 8}",
            "additional test 2 - not part of text]",
        ),
        (
            "UnrankPermutation[9!-1, 9]",
            "{9, 8, 7, 6, 5, 4, 3, 2, 1}",
            "additional test 3 - not part of text]",
        ),
        (
            "p=RandomPermutation[50]; "
            "Inversions[p] == Inversions[InversePermutation[p]]",
            "True",
            "inversions, 1.1.1, Page 4",
        ),
        (
            "NecklacePolynomial[6, {a, b, c}, Cyclic]",
            "a ^ 6 + a ^ 5 b + a ^ 5 c + 3 a ^ 4 b ^ 2 + 5 a ^ 4 b c + "
            "3 a ^ 4 c ^ 2 + 4 a ^ 3 b ^ 3 + 10 a ^ 3 b ^ 2 c + "
            "10 a ^ 3 b c ^ 2 + 4 a ^ 3 c ^ 3 + 3 a ^ 2 b ^ 4 + 10 a ^ 2 b ^ 3 c + "
            "16 a ^ 2 b ^ 2 c ^ 2 + 10 a ^ 2 b c ^ 3 + 3 a ^ 2 c ^ 4 + a b ^ 5 + "
            "5 a b ^ 4 c + 10 a b ^ 3 c ^ 2 + 10 a b ^ 2 c ^ 3 + 5 a b c ^ 4 + "
            "a c ^ 5 + b ^ 6 + b ^ 5 c + 3 b ^ 4 c ^ 2 + 4 b ^ 3 c ^ 3 + "
            "3 b ^ 2 c ^ 4 + b c ^ 5 + c ^ 6",
            "Necklace polynomial, 1.1.1 Page 4",
        ),
        (
            "Subsets[{1,2,3,4}]",
            "{{}, {4}, {3, 4}, {3}, {2, 3}, {2, 3, 4}, {2, 4}, "
            "{2}, {1, 2}, {1, 2, 4}, {1, 2, 3, 4}, {1, 2, 3}, "
            "{1, 3}, {1, 3, 4}, {1, 4}, {1}}",
            "all 4-element subsets, minimum change order; 1.1.1, Page 5",
        ),
        (
            "KSubsets[{1,2,3,4,5}, 3]",
            "{{1, 2, 3}, {1, 2, 4}, {1, 2, 5}, {1, 3, 4}, {1, 3, 5}, "
            "{1, 4, 5}, {2, 3, 4}, {2, 3, 5}, {2, 4, 5}, {3, 4, 5}}",
            "k subsets, 1.1.1, Page 5",
        ),
    ):
        check_evaluation(str_expr, str_expected, message)


def test_partitions_compositions_and_young_tableaux_1_1_2():
    for str_expr, str_expected, message in (
        (
            "Partitions[6]",
            " {{6}, {5, 1}, {4, 2}, {4, 1, 1}, "
            "{3, 3}, {3, 2, 1}, {3, 1, 1, 1}, "
            "{2, 2, 2}, {2, 2, 1, 1}, {2, 1, 1, 1, 1}, "
            "{1, 1, 1, 1, 1, 1}}",
            "partitions, 1.1.2 Page 7",
        ),
        (
            "Compositions[5, 3]",
            "{{0, 0, 5}, {0, 1, 4}, {0, 2, 3}, {0, 3, 2}, "
            "{0, 4, 1}, {0, 5, 0}, {1, 0, 4}, {1, 1, 3}, {1, 2, 2}, "
            "{1, 3, 1}, {1, 4, 0}, {2, 0, 3}, {2, 1, 2}, {2, 2, 1}, "
            "{2, 3, 0}, {3, 0, 2}, {3, 1, 1}, {3, 2, 0}, {4, 0, 1}, "
            "{4, 1, 0}, {5, 0, 0}}",
            "Compositions, 1.1.2 Page 7",
        ),
        (
            "SetPartitions[3]",
            "{{{1, 2, 3}}, {{1}, {2, 3}}, {{1, 2}, {3}}, "
            "{{1, 3}, {2}}, {{1}, {2}, {3}}}",
            "Set partitions, 1.1.2 Page 7",
        ),
        # (
        #     "Tableaux[{2,2,1}]",
        #     "???",
        #     "Tableaux, 1.1.2 Page 8",
        # ),
    ):
        check_evaluation(str_expr, str_expected, message, to_string_expr=True)


def test_inversions_and_inversion_vectors_1_3():
    for str_expr, str_expected, message in (
        (
            "p = {5,9,1,8,2,6,4,7,3}; ToInversionVector[p]",
            "{2, 3, 6, 4, 0, 2, 2, 1}",
            "ToInversionVector 1.3.1, Page 27",
        ),
        (
            "FromInversionVector[ToInversionVector[p]]",
            "p",
            "FromInversionVector 1.3.1, Page 28",
        ),
        # (
        #     "h = InversePermutation[p]; "
        #     "g = MakeGraph[Range[Length[p]], ((#1<#2 && h[[#1]]>h[[#2]]) || (#1>#2 && h[[#1]]<h[[#2]]))&]; "
        #     "Inversions[p]",
        #     "M[g]",
        #     "Edges equals # of inversions 1.3.1, Page 28",
        # ),
        (
            "Inversions[p]",
            "Inversions[InversePermutation[p]]",
            "[Knu73b] 1.3.2, Page 29",
        ),
        (
            "Inversions[Reverse[Range[8]]]",
            "Binomial[8, 2]",
            "# permutations is [0 .. Binomial(n 2)]; largest is reverse 1.3.2, Page 29",
        ),
        (
            "Union [ Map[Inversions, Permutations[Range[4]]] ]",
            "Range[0, 6]",
            "Every one is realizable as ... 1.3.2, Page 29",
        ),
        (
            "p = RandomPermutation[6]; Inversions[p] + Inversions[Reverse[p]]",
            "Binomial[Length[p], 2]",
            "A neat proof that ... 1.3.2, Page 29",
        ),
        (
            "Select[Permutations[Range[4]], (Inversions[#]==3)&]",
            "{{1, 4, 3, 2}, {2, 3, 4, 1}, {2, 4, 1, 3},"
            " {3, 1, 4, 2}, {3, 2, 1, 4}, {4, 1, 2, 3}}",
            "MacMahon theorem, 1.3.3 Page 30",
        ),
        (
            "Select[Permutations[Range[4]], (Length[Runs[#]]==2)&]",
            "{{1, 2, 4, 3}, {1, 3, 2, 4}, {1, 3, 4, 2}, {1, 4, 2, 3},"
            " {2, 1, 3, 4}, {2, 3, 1, 4}, {2, 3, 4, 1}, {2, 4, 1, 3},"
            " {3, 1, 2, 4}, {3, 4, 1, 2}, {4, 1, 2, 3}}",
            "11 permutations of length 4 with 2 runs, 1.3.4, Page 31",
        ),
        (
            "Eulerian[4,2]",
            "11",
            "Eulerian from [Knu73b], 1.3.4 Page 31",
        ),
    ):
        check_evaluation(str_expr, str_expected, message)


# def test_special_classes_of_permutations_1_4():
#     # We include this earlier since the above in fact rely on KSubsets
#     for str_expr, str_expected, message in (
#         (
#             "Map[ ToCycles, Select[ Permutations[Range[4]], InvolutionQ ] ]",
#             "{{{1}, {2}, {3}, {4}}, {{1}, {2}, {4, 3}}, "
#             "{{1}, {3, 2}, {4}}, {{1}, {4, 2}, {3}}, "
#             "{{2, 1}, {3}, {4}}, {{2, 1}, {4, 3}}, "
#             "{{3, 1}, {2}, {4}}, {{3, 1}, {4, 2}}, "
#             "{{4, 1}, {2}, {3}}, {{4, 1}, {3, 2}}}",
#             "Involutions; 1.4.1, Page 33",
#         ),
#         (
#             "NumberOfInvolutions[4]",
#             "10",
#             "NumberOfInvolutions; 1.4.1, Page 33",
#         ),
#         (
#             "Table[NumberOfDerangements[i], {i, 1, 10}]",
#             "{0, 1, 2, 9, 44, 265, 1854, 14833, 133496, 1334961}",
#             "NumberOfDerangements; 1.4.2, Page 33",
#         ),
#         (
#             "Table[ N[ NumberOfDerangements[i]/(i!) ], {i, 1, 10} ]",
#             "{0., 0.5, 0.333333, 0.375, 0.366667, 0.368056, 0.367857, 0.367882, 0.367879, 0.367879}",
#             "Confused Secretary 1.4.2, Page 34",
#         ),
#         (
#             "Table[Round[n!/N[E]], {n, 1, 10}]",
#             "{0, 1, 2, 9, 44, 265, 1854, 14833, 133496, 1334961}",
#             "Rounding as a nicer way to get derangmeants; 1.4.2, Page 34",
#         ),
#         (
#             "Josephus[17, 7]",
#             "{16, 17, 5, 3, 14, 7, 1, 11, 10, 12, 9, 4, 6, 2, 15, 13, 8}",
#             "Josephus; 1.4.3, Page 35",
#         ),
#         # FIXME: Note RandomPermutation1 for large numbers isn't random
#         # Therefore in combinatorica we use RandomPermutation2.
#         (
#             "HeapSort[Reverse[Range[10]]]",
#             "Range[10]",
#             "Heapsort test 1; 1.4.4, Page 38",
#         ),
#         (
#             "HeapSort[RandomPermutation[10]]",
#             "Range[10]",
#             "Heapsort test 2; 1.4.4, Page 38",
#         ),
#     ):
#         check_evaluation(str_expr, str_expected, message)


# def test_combinations_1_5():
#     # We include this earlier since the above in fact rely on KSubsets
#     for str_expr, str_expected, message in (
#         (
#             "Strings[Range[3], 3]",
#             "{{1, 1, 1}, {1, 1, 2}, {1, 1, 3}, {1, 2, 1}, "
#             " {1, 2, 2}, {1, 2, 3}, {1, 3, 1}, {1, 3, 2}, {1, 3, 3}, "
#             " {2, 1, 1}, {2, 1, 2}, {2, 1, 3}, {2, 2, 1}, {2, 2, 2}, "
#             " {2, 2, 3}, {2, 3, 1}, {2, 3, 2}, {2, 3, 3}, {3, 1, 1}, "
#             " {3, 1, 2}, {3, 1, 3}, {3, 2, 1}, {3, 2, 2}, {3, 2, 3}, "
#             " {3, 3, 1}, {3, 3, 2}, {3, 3, 3}}",
#             "String 1.5.1, Page 40",
#         ),
#         (
#             "BinarySubsets[{a,b,c,d}]",
#             "{{}, {a}, {b}, {a, b}, {c}, {a, c}, {b, c}, "
#             "{a, b, c}, {d}, {a, d}, {b, d}, {a, b, d}, {c, d}, "
#             "{a, c, d}, {b, c, d}, {a, b, c, d}}",
#             "BinarySubsets 1.5.2, Page 41",
#         ),
#         (
#             "Table[NthSubset[n, {a,b,c,d}], {n, 0, 15}]",
#             "{{}, {a}, {b}, {a, b}, {c}, {a, c}, {b, c}, "
#             "{a, b, c}, {d}, {a, d}, {b, d}, {a, b, d}, {c, d}, "
#             "{a, c, d}, {b, c, d}, {a, b, c, d}}",
#             "NthSubset 1.5.2, Page 451",
#         ),
#         (
#             "NthSubset[-10, {a, b, c, d}]",
#             "{b, c}",
#             "NthSubset 1.5.2, Page 41",
#         ),
#         (
#             "Map[ (RankSubset[Range[4], #])&, BinarySubsets[Range[4]] ]",
#             "Range[0, 15]",
#             "RankSubset 1.5.2, Page 42",
#         ),
#         (
#             "GrayCode[Range[4]]",
#             "{{}, {1}, {1, 2}, {2}, {2, 3}, {1, 2, 3}, "
#             "{1, 3}, {3}, {3, 4}, {1, 3, 4}, {1, 2, 3, 4}, "
#             "{2, 3, 4}, {2, 4}, {1, 2, 4}, {1, 4}, {4}}",
#             "GrayCode 1.5.3, Page 43",
#         ),
#         (
#             "LexicographicSubsets[Range[4]]",
#             "{{}, {1}, {1, 2}, {1, 2, 3}, {1, 2, 3, 4}, "
#             "{1, 2, 4}, {1, 3}, {1, 3, 4}, {1, 4}, {2}, {2, 3}, "
#             "{2, 3, 4}, {2, 4}, {3}, {3, 4}, {4}}",
#             "LexicographicSubsets 1.5.4, Page 44",
#         ),
#         (
#             "KSubsets[Range[3], 0]",
#             "{ {} } ",
#             "KSubsets[0] == { {} }",
#         ),
#         (
#             "KSubsets[Range[5], 1]",
#             "{{1}, {2}, {3}, {4}, {5}}",
#             "KSubsets[Range[n, 1] == Partition[n]",
#         ),
#         (
#             "KSubsets[Range[5], 3]",
#             "{{1, 2, 3}, {1, 2, 4}, {1, 2, 5}, {1, 3, 4}, "
#             "{1, 3, 5}, {1, 4, 5}, {2, 3, 4}, {2, 3, 5}, {2, 4, 5}, "
#             "{3, 4, 5}}",
#             "KSubsets 1.5.5, Page 44",
#         ),
#         (
#             "KSubsets[Range[5], 5]",
#             "{Range[5]} ",
#             "KSubsets[l, k] == Length(l)",
#         ),
#     ):
#         check_evaluation(str_expr, str_expected, message)


def test_2_1_to_2_3():
    for str_expr, str_expected, failure_message, hold_expected in (
        (
            # 2.1.1 uses Partitions which is broken
            # 2.1.2 Ferrers Diagrams can't be tested easily and robustly here
            # easily
            # 2.1.3 uses Partitions which is broken
            "PartitionsP[10]",
            "NumberOfPartitions[10]",
            "Counting Partitions 2.1.4, Page 57",
            False,
        ),
        (
            "NumberOfCompositions[6,3]",
            "28",
            "Random Compositions 2.2.1, Page 60",
            False,
        ),
        (
            "TableauQ[{{1,2,5}, {3,4,5}, {6}}]",
            "True",
            "Young Tableau 2.3, Page 64",
            False,
        ),
        (
            "TableauQ[{{1,2,5,9,10}, {5,4,7,13}, {4,8,12},{11}}]",
            "False",
            "Young Tableau 2.3, Page 64",
            False,
        ),
        (
         "TableForm[ {{1,2,5}, {3,4,5}, {6}} ]",
         """{1, 2, 5}\n\n{3, 4, 5}\n\n{6}\n""",
        "Young Tableau 2.3, Page 63",
         True,
         ),
    ):
        check_evaluation(str_expr, str_expected,  failure_message, hold_expected)


def test_combinatorica_rest():
    for str_expr, str_expected, message in (
        # (
        #     "Permute[{A, B, C, D}, Permutations[Range[3]]]",
        #     "{{A, B, C}, {A, C, B}, {B, A, C}, {B, C, A}, {C, A, B}, {C, B, A}}",
        #     "Permute",
        # ),
        # (
        #     "Subsets[Range[3]]",
        #     "{{}, {1}, {2}, {3}, {1, 2}, {1, 3}, {2, 3}, {1, 2, 3}}",
        #     "Subsets",
        # ),
        # (
        #     "BinarySearch[{2, 3, 9}, 7] // N",
        #     "2.5",
        #     "BinarySearch - mid-way insertion point",
        # ),
        # ("BinarySearch[{3, 4, 10, 100, 123}, 100]", "4", "BinarySearch find item"),
        # (
        #     "BinarySearch[{2, 3, 9}, 7] // N",
        #     "2.5",
        #     "BinarySearch - mid-way insertion point",
        # ),
        # (
        #     "BinarySearch[{2, 7, 9, 10}, 3] // N",
        #     "1.5",
        #     "BinarySearch - insertion point after 1st item",
        # ),
        # (
        #     "BinarySearch[{-10, 5, 8, 10}, -100] // N",
        #     "0.5",
        #     "BinarySearch find before first item",
        # ),
        # (
        #     "BinarySearch[{-10, 5, 8, 10}, 20] // N",
        #     "4.5",
        #     "BinarySearch find after last item",
        # ),
        # (
        #     "BinarySearch[{{a, 1}, {b, 7}}, 7, #[[2]]&]",
        #     "2",
        #     "BinarySearch - find where key is a list",
        # ),
        (
            "SetPartitions[3]",
            "{{{1, 2, 3}}, {{1}, {2, 3}}, {{1, 2}, {3}}, {{1, 3}, {2}}, {{1}, {2}, {3}}}",
            "SetPartitions"
        ),
        (
            "TransposePartition[{8, 6, 4, 4, 3, 1}]",
            "{6, 5, 5, 4, 2, 2, 1, 1}",
            "TransposePartition",
        ),
    ):
        check_evaluation(str_expr, str_expected, message)
