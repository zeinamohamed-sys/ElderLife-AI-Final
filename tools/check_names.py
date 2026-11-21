"""Static check (pyflakes-lite): reports names that are used but never defined/imported in scope, and imports that are never used.
Used because FastAPI/SQLAlchemy cannot be installed offline in some environments. Usage: python tools/check_names.py <dir-or-file> ..."""
import ast, builtins, sys, pathlib
BUILT = set(dir(builtins)) | {"__file__", "__name__", "__doc__"}
class Scope:
    def __init__(self, kind, parent=None): self.kind, self.parent, self.names = kind, parent, set()
def bind_targets(t, s):
    for x in ast.walk(t):
        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store): s.names.add(x.id)
def collect(node, s):
    """collect names bound directly in this scope (not descending into nested function/class scopes)"""
    for ch in ast.iter_child_nodes(node):
        if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): s.names.add(ch.name); continue
        if isinstance(ch, ast.Lambda): continue
        if isinstance(ch, (ast.Import, ast.ImportFrom)):
            for a in ch.names: s.names.add((a.asname or a.name).split(".")[0])
        elif isinstance(ch, ast.Name) and isinstance(ch.ctx, ast.Store): s.names.add(ch.id)
        elif isinstance(ch, ast.ExceptHandler) and ch.name: s.names.add(ch.name)
        elif isinstance(ch, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for g in ch.generators: bind_targets(g.target, s)
        elif isinstance(ch, ast.NamedExpr): s.names.add(ch.target.id)
        collect(ch, s)
def check_file(path):
    src = pathlib.Path(path).read_text(encoding="utf-8"); tree = ast.parse(src); problems = []; used = set()
    modscope = Scope("module"); collect(tree, modscope); imported = {}
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names: imported[(a.asname or a.name).split(".")[0]] = n.lineno
    def visit(node, scope):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            for d in getattr(node, "decorator_list", []): visit(d, scope)
            a = node.args
            for d in a.defaults + [x for x in a.kw_defaults if x]: visit(d, scope)
            if not isinstance(node, ast.Lambda):
                for arg in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg]:
                    if arg and arg.annotation: visit(arg.annotation, scope)
                if node.returns: visit(node.returns, scope)
            s = Scope("func", scope)
            for arg in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg]:
                if arg: s.names.add(arg.arg)
            body = node.body if isinstance(node.body, list) else [node.body]
            holder = ast.Module(body=body if isinstance(node.body, list) else [ast.Expr(node.body)], type_ignores=[]); collect(holder, s)
            for st in holder.body: visit(st, s)
            return
        if isinstance(node, ast.ClassDef):
            for d in node.decorator_list + node.bases + [k.value for k in node.keywords]: visit(d, scope)
            s = Scope("class", scope); collect(node, s)
            for st in node.body: visit(st, s)
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            s = Scope("comp", scope)
            for g in node.generators: bind_targets(g.target, s)
            for ch in ast.iter_child_nodes(node): visit(ch, s)
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id); sc = scope; found = False; first = True
            while sc:
                if node.id in sc.names and (sc.kind != "class" or first): found = True; break
                first = False; sc = sc.parent
            if not found and node.id not in BUILT: problems.append(f"{path}:{node.lineno}: undefined name '{node.id}'")
        for ch in ast.iter_child_nodes(node): visit(ch, scope)
    for st in tree.body: visit(st, modscope)
    # names used only in string annotations / __all__ are not handled; main.py re-exports are ignored via noqa marker
    if "noqa: reexport" not in src:
        for name, ln in imported.items():
            if name not in used and not path.endswith("__init__.py") and "noqa" not in src.splitlines()[ln-1]: problems.append(f"{path}:{ln}: unused import '{name}'")
    return problems
if __name__ == "__main__":
    files = []
    for a in sys.argv[1:]:
        p = pathlib.Path(a); files += sorted(p.rglob("*.py")) if p.is_dir() else [p]
    out = [x for f in files for x in check_file(str(f))]
    print("\n".join(out) or "no problems found"); sys.exit(1 if out else 0)
