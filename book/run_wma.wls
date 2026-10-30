(* Run notebook input cells under WMA's Combinatorica`, appending one JSON line per cell.
   args: cells.json out.jsonl seed timeout start *)
{H`inf, H`outf, H`seed, H`tmo, H`start} = Rest[$ScriptCommandLine];
{H`seed, H`tmo, H`start} = ToExpression[{H`seed, H`tmo, H`start}];
Off[General::compat, General::shdw, SetDelayed::write, Set::write, SetDelayed::wrsym];
Needs["Combinatorica`"];
On[SetDelayed::write, Set::write, SetDelayed::wrsym];
SeedRandom[H`seed];
H`canon[r_] := Which[
   MatchQ[r, _Graphics | _Graphics3D | _GraphicsArray | _Image], "<" <> SymbolName[Head[r]] <> ">",
   True, Module[{s = ToString[FullForm[r /. x_Real :> Round[10^5 x]]]},
     If[StringLength[s] > 4000, StringTake[s, 4000] <> "...", s]]];
H`cells = Import[H`inf, "RawJSON"];
H`str = OpenAppend[H`outf];
(* The loop counter lives in H` : a cell may use or set a global i. *)
Do[
  Module[{d, c = H`cells[[H`i]], held},
   WriteString[$Output, "start ", H`i, "\n"];
   held = ToExpression[c["in"], InputForm, Hold];
   (* A cell may hold several expressions: all are evaluated, the last is the result. *)
   d = EvaluationData[TimeConstrained[Last[List @@ First[held]], H`tmo, $TimedOut]];
   WriteString[H`str, ExportString[<|"i" -> H`i, "sec" -> c["sec"], "in" -> c["in"],
      "out" -> ToString[H`canon[d["Result"]]],
      "msgs" -> (ToString[#, InputForm] & /@ d["Messages"]),
      "secs" -> N[d["AbsoluteTiming"]],
      "status" -> Which[d["Result"] === $TimedOut, "timeout", d["Messages"] =!= {}, "msg", True, "ok"]|>,
      "RawJSON", "Compact" -> True], "\n"]],
  {H`i, H`start, Length[H`cells]}];
Close[H`str];
