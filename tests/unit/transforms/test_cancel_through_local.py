"""Tests for CancelThroughLocal."""

from proof_frog import frog_ast, frog_parser
from proof_frog.transforms._base import PipelineContext
from proof_frog.transforms.algebraic import CancelThroughLocal
from proof_frog.visitors import NameTypeMap


def _ctx() -> PipelineContext:
    lets = NameTypeMap()
    q = frog_ast.Variable("q")
    lets.set("q", frog_ast.IntType())
    lets.set("H", frog_ast.FunctionType(frog_ast.ModIntType(q), frog_ast.ModIntType(q)))
    return PipelineContext(
        variables={}, proof_let_types=lets, proof_namespace={}, subsets_pairs=[]
    )


def _lines(game: frog_ast.Game) -> list[str]:
    return [str(s).strip() for s in game.methods[0].block.statements]


def test_cancels_through_a_local() -> None:
    game = frog_parser.parse_game("""
        Game T(Int q) {
            ModInt<q> sk;
            [ModInt<q>, ModInt<q>] Upd(ModInt<q> d, ModInt<q> x) {
                ModInt<q> v = d + H(x);
                sk = sk + (v - H(x));
                return [sk, v];
            }
        }
        """)
    result = CancelThroughLocal().apply(game, _ctx())
    assert _lines(result) == [
        "ModInt<q> v = d + H(x);",
        "sk = d + sk;",
        "return [sk, v];",
    ]


def test_f370_no_fire_on_a_local_shadowing_a_field() -> None:
    # F-370(a), case C2: the local v's initializer reads the field v. The
    # return's v is the local, but substituting v + d for it gives v, which
    # the return would read as the local again: v - d is not v.
    game = frog_parser.parse_game("""
        Game T(Int q) {
            ModInt<q> v;
            ModInt<q> Get(ModInt<q> d) {
                ModInt<q> v = v + d;
                return v - d;
            }
        }
        """)
    assert CancelThroughLocal().apply(game, _ctx()) == game
