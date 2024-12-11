Here we have all the programs from the book, "Computational
Discrete Mathematics: Combinatorics and Graph Theory in Mathematica",
by Sriram V. Pemmaraju and Steven S. Skiena, Cambridge University Press,
2003.

To run from inside Mathics3::

        $ git clone git@github.com:Mathic3/Mathics3-Combinatorica.git
        $ cd Mathics3-Combinatorica

        $ mathics

        Mathics 7.0.1dev0
        on CPython 3.12.10 ...
        ...
        In[1]:= << CombinatoricaV2.0.0.m
	...

	In[2]:= Permutations[3]
	Out[2]= {{1, 2, 3}, {1, 3, 2}, {2, 1, 3}, {2, 3, 1}, {3, 1, 2}, {3, 2, 1}}

	In[3]:= Permute[{A,B,C,D}, Permutations[3]]
	Out[3]= {{A, B, C}, {A, C, B}, {B, A, C}, {B, C, A}, {C, A, B}, {C, B, A}}
