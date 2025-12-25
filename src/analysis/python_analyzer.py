"""
Module for analyzing Python code files - UPDATED with numerical metrics extraction.
"""

import ast
import os
import re
import subprocess
import math
import statistics
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any, List, Set, Tuple

class PythonCodeAnalyzer:
    """Analyzer for Python source code files."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.tree = None
        self.content = ""
        self.lines = []
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze the Python file and extract ALL metrics."""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            self.content = f.read()
        
        self.lines = self.content.split('\n')
        self.tree = ast.parse(self.content)
        
        # Extract ALL metrics
        # compute base metrics
        self.metrics = {
            "file_info": self._get_file_info(),
            "size_metrics": self._get_size_metrics(),
            "structure_metrics": self._get_structure_metrics(),
            "complexity_metrics": self._get_complexity_metrics(),
            "function_metrics": self._get_function_metrics(),
            "class_metrics": self._get_class_metrics(),
            "import_analysis": self._get_import_analysis(),
            "documentation_metrics": self._get_documentation_metrics(),
            "object_oriented_metrics": self._get_object_oriented_metrics(),
        }

        # optional/derived metrics
        self.metrics["call_graph_metrics"] = self._compute_call_graph_metrics()
        self.metrics["boolean_expression_metrics"] = self._boolean_expression_metrics()
        self.metrics["attribute_mutations"] = self._attribute_mutation_outside_constructor()
        self.metrics["global_state_usage"] = self._global_state_usage()
        self.metrics["cyclomatic_param_metrics"] = self._cyclomatic_ratio_and_param_entropy()
        self.metrics["abbrev_mismatch_metrics"] = self._abbrev_and_comment_mismatch()
        self.metrics["halstead_metrics"] = self._halstead_metrics()
        self.metrics["style_metrics"] = self._style_metrics()
        self.metrics["test_metrics"] = self._test_metrics()
        self.metrics["semantic_metrics"] = self._semantic_textual_metrics()
        self.metrics["vcs_metrics"] = self._get_vcs_metrics()

        self.metrics["numerical_summary"] = self._get_numerical_summary()
        
        return self.metrics
    
    def _get_file_info(self) -> Dict[str, Any]:
        return {
            "filename": os.path.basename(self.filepath),
            "file_size_bytes": os.path.getsize(self.filepath),
            "encoding": "utf-8"
        }
    
    def _get_size_metrics(self) -> Dict[str, int | float]:
        total_lines = len(self.lines)

        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        docstring_lines = 0

        # Identify docstring ranges using AST (more robust than naive quote counting)
        doc_ranges: List[Tuple[int, int]] = []
        if self.tree is None:
            return {
                "LOC": total_lines,
                "SLOC": 0,
                "CLOC": 0,
                "DLOC": 0,
                "blank_lines": 0,
                "comment_density": 0
            }
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                ds = ast.get_docstring(node)
                if ds is not None and getattr(node, 'body', None):
                    first = node.body[0]
                    if isinstance(first, ast.Expr) and hasattr(first, 'lineno'):
                        start = first.lineno - 1
                        end = getattr(first, 'end_lineno', start)
                        # ensure end is inclusive line index
                        doc_ranges.append((start, end - 1))

        # merge ranges
        merged: List[Tuple[int, int]] = []
        for s, e in sorted(doc_ranges):
            if not merged or s > merged[-1][1] + 1:
                merged.append((s, e))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))

        doc_lines_set = set()
        for s, e in merged:
            for i in range(s, e + 1):
                if 0 <= i < total_lines:
                    doc_lines_set.add(i)

        for idx, line in enumerate(self.lines):
            if idx in doc_lines_set:
                docstring_lines += 1
                continue
            stripped = line.strip()
            if stripped == '':
                blank_lines += 1
            elif stripped.startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1
        
        return {
            "LOC": total_lines,
            "SLOC": code_lines,
            "CLOC": comment_lines,
            "DLOC": docstring_lines,
            "blank_lines": blank_lines,
            "comment_density": comment_lines / total_lines if total_lines > 0 else 0
        }
    
    def _get_complexity_metrics(self) -> Dict[str, Any]:
        # Calculate complexity metrics using a recursive visitor to track nesting
        max_nesting = 0
        total_decisions = 0
        per_function_nesting = []

        control_types = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.IfExp)

        def visit(node: ast.AST, depth: int = 0):
            nonlocal max_nesting, total_decisions
            is_control = isinstance(node, control_types)
            if is_control:
                total_decisions += 1
                depth += 1
                max_nesting = max(max_nesting, depth)

            # reset depth when entering a new function/class
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node is not self.tree:
                child_depth = 0
            else:
                child_depth = depth

            for child in ast.iter_child_nodes(node):
                visit(child, child_depth)

        # compute global and per-function nesting
        if self.tree is not None:
            visit(self.tree, 0)
            # per-function nesting: compute max nesting inside each function
            for node in ast.walk(self.tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    local_max = 0

                    def visit_f(n, depth=0):
                        nonlocal local_max
                        if isinstance(n, control_types):
                            depth += 1
                            local_max = max(local_max, depth)
                        for c in ast.iter_child_nodes(n):
                            visit_f(c, depth)

                    visit_f(node, 0)
                    per_function_nesting.append(local_max)

        estimated_cyclomatic = total_decisions + 1

        nesting_variance = statistics.pstdev(per_function_nesting) if per_function_nesting else 0
        nesting_mean = statistics.mean(per_function_nesting) if per_function_nesting else 0

        return {
            "max_nesting_level": max_nesting,
            "total_control_structures": total_decisions,
            "estimated_cyclomatic_complexity": estimated_cyclomatic,
            "average_cyclomatic_per_function": estimated_cyclomatic / max(1, self._get_structure_metrics()["functions"]),
            "per_function_nesting": per_function_nesting,
            "nesting_mean": round(nesting_mean, 3),
            "nesting_variance": round(nesting_variance, 3)
        }
    
    def _get_structure_metrics(self) -> Dict[str, int]:
        class_count = 0
        function_count = 0
        async_function_count = 0
        
        if self.tree is None:
            return {
                "classes": 0,
                "functions": 0,
                "async_functions": 0,
                "total_elements": 0
            }
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                class_count += 1
            elif isinstance(node, ast.FunctionDef):
                function_count += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                async_function_count += 1
        
        return {
            "classes": class_count,
            "functions": function_count,
            "async_functions": async_function_count,
            "total_elements": class_count + function_count + async_function_count
        }
    
    def _get_function_metrics(self) -> List[Dict[str, Any]]:
        functions = []
        # detect methods (functions defined inside classes)
        method_nodes = set()
        
        if self.tree is None:
            return []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_nodes.add(item)

        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cc = self._compute_cyclomatic_complexity(node)
                calls = self._collect_calls(node)

                # function LOC
                if hasattr(node, 'end_lineno') and node.end_lineno is not None and node.lineno is not None:
                    func_loc = node.end_lineno - node.lineno + 1
                else:
                    # best-effort: count number of AST nodes as proxy
                    func_loc = sum(1 for _ in ast.walk(node))

                # attribute access counts
                internal_attr_access = 0
                external_attr_access = 0
                for n in ast.walk(node):
                    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                        if n.value.id == 'self':
                            internal_attr_access += 1
                        else:
                            external_attr_access += 1

                # number of calls
                num_calls = len(calls)

                func_info = {
                    "name": node.name,
                    "args_count": len(node.args.args),
                    "default_args": len(node.args.defaults),
                    "lineno": getattr(node, 'lineno', None),
                    "has_decorators": len(getattr(node, 'decorator_list', [])) > 0,
                    "has_docstring": ast.get_docstring(node) is not None,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "is_method": node in method_nodes,
                    "calls_made": sorted(list(calls)),
                    "num_calls": num_calls,
                    "cyclomatic_complexity": cc,
                    "loc": func_loc,
                    "cc_loc_ratio": round(cc / max(1, func_loc), 3),
                    "internal_attr_access": internal_attr_access,
                    "external_attr_access": external_attr_access,
                    "feature_envy_ratio": round((external_attr_access / max(1, internal_attr_access + 1)), 3)
                }
                functions.append(func_info)
        
        return functions

    def _compute_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Estimate cyclomatic complexity for a function/method AST node."""
        decisions = 0
        for n in ast.walk(node):
            if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.IfExp, ast.BoolOp, ast.ExceptHandler, ast.comprehension)):
                decisions += 1
        return decisions + 1

    def _collect_calls(self, node: ast.AST) -> Set[str]:
        """Collect called function/method names (approximate)."""
        calls = set()
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                # try to get name
                func = n.func
                if isinstance(func, ast.Name):
                    calls.add(func.id)
                elif isinstance(func, ast.Attribute):
                    parts = []
                    cur = func
                    while isinstance(cur, ast.Attribute):
                        parts.append(cur.attr)
                        cur = cur.value
                    if isinstance(cur, ast.Name):
                        parts.append(cur.id)
                    calls.add(".".join(reversed(parts)))
        return calls
    
    def _get_class_metrics(self) -> Dict[str, Any]:
        classes = []
        
        if self.tree is None:
            return {"total_classes": 0}
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # Count methods in class
                methods_nodes = [item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
                methods = len(methods_nodes)
                attributes = sum(1 for item in node.body if isinstance(item, ast.Assign) or isinstance(item, ast.AnnAssign))
                
                # ratio: few methods many attributes -> lazy/data class
                lazy_ratio = attributes / max(1, methods)

                # feature envy proxy: per-class external call ratio
                external_calls = 0
                internal_calls = 0
                for m in methods_nodes:
                    calls = self._collect_calls(m)
                    for c in calls:
                        if '.' in c and not c.startswith('self'):
                            external_calls += 1
                        else:
                            internal_calls += 1

                class_info = {
                    "name": node.name,
                    "methods": methods,
                    "attributes": attributes,
                    "lazy_ratio": round(lazy_ratio, 3),
                    "external_calls": external_calls,
                    "internal_calls": internal_calls,
                    "has_inheritance": len(node.bases) > 0,
                    "has_docstring": ast.get_docstring(node) is not None,
                    "line_count": 0
                }
                
                if hasattr(node, 'end_lineno') and node.end_lineno is not None and node.lineno is not None:
                    class_info["line_count"] = node.end_lineno - node.lineno
                
                classes.append(class_info)        
        if not classes:
            return {"total_classes": 0}
        
        return {
            "total_classes": len(classes),
            "classes": classes,
            "average_methods_per_class": sum(c["methods"] for c in classes) / len(classes),
            "classes_with_inheritance": sum(1 for c in classes if c["has_inheritance"]),
            "classes_with_docstrings": sum(1 for c in classes if c["has_docstring"])
        }


    
    def _get_import_analysis(self) -> Dict[str, Any]:
        imports = []
        import_froms = []
        
        if self.tree is None:
            return {
                "imports": imports,
                "import_froms": import_froms,
                "total_imports": 0
            }
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    import_froms.append(f"{module}.{alias.name}")
        
        return {
            "imports": imports,
            "import_froms": import_froms,
            "total_imports": len(imports) + len(import_froms)
        }
    
    def _get_documentation_metrics(self) -> Dict[str, Any]:
        """Analyze documentation quality."""
        function_with_docstring = 0
        class_with_docstring = 0
        total_functions = 0
        total_classes = 0
        
        if self.tree is None:
            return {
                "functions_with_docstrings": 0,
                "classes_with_docstrings": 0,
                "total_documented_elements": 0,
                "documentation_coverage": 0
            }
        
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_functions += 1
                if ast.get_docstring(node):
                    function_with_docstring += 1
            elif isinstance(node, ast.ClassDef):
                total_classes += 1
                if ast.get_docstring(node):
                    class_with_docstring += 1
        
        total_elements = total_functions + total_classes
        documented_elements = function_with_docstring + class_with_docstring
        
        return {
            "functions_with_docstrings": function_with_docstring,
            "classes_with_docstrings": class_with_docstring,
            "total_documented_elements": documented_elements,
            "documentation_coverage": documented_elements / max(1, total_elements)
        }
    
    def _get_object_oriented_metrics(self) -> Dict[str, Any]:
        """Extract object-oriented metrics."""
        # Build map of class name -> node for resolution
        class_map: Dict[str, ast.ClassDef] = {}
        
        if self.tree is None:
            return {
                "total_classes": 0,
                "average_methods_per_class": 0,
                "classes_with_inheritance": 0,
                "average_inheritance_depth": 0
            }
        
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                class_map[node.name] = node

        if not class_map:
            return {
                "total_classes": 0,
                "average_methods_per_class": 0,
                "classes_with_inheritance": 0,
                "average_inheritance_depth": 0
            }

        def inheritance_depth(cnode: ast.ClassDef, seen: Set[str] | None = None) -> int:
            if seen is None:
                seen = set()
            if cnode.name in seen:
                return 0
            seen.add(cnode.name)
            depth = 0
            for base in cnode.bases:
                if isinstance(base, ast.Name) and base.id in class_map:
                    depth = max(depth, 1 + inheritance_depth(class_map[base.id], seen))
                else:
                    depth = max(depth, 1)
            return depth

        results = []

        for cname, cnode in class_map.items():
            methods = [m for m in cnode.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            method_names = [m.name for m in methods]

            # collect class-level attributes
            class_fields = set()
            for item in cnode.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            class_fields.add(target.id)
                elif isinstance(item, ast.AnnAssign):
                    if isinstance(item.target, ast.Name):
                        class_fields.add(item.target.id)

            # instance fields assigned to self in methods
            instance_fields = set()
            method_field_access: Dict[str, Set[str]] = {}
            method_calls: Dict[str, Set[str]] = {}

            for m in methods:
                accessed = set()
                calls = set()
                for node in ast.walk(m):
                    # self.x accesses
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
                        accessed.add(node.attr)
                    # assignments to self.x
                    if isinstance(node, ast.Assign):
                        for t in node.targets:
                            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == 'self':
                                instance_fields.add(t.attr)
                    # collect calls
                calls = self._collect_calls(m)
                method_field_access[m.name] = accessed
                method_calls[m.name] = calls

            total_fields = class_fields.union(instance_fields)

            # WMC: sum of cyclomatic complexity of methods
            wmc = sum(self._compute_cyclomatic_complexity(m) for m in methods)

            # LCOM: number of method pairs without shared fields vs with shared fields
            m = len(methods)
            if m <= 1:
                lcom = 0.0
            else:
                pairs = 0
                shared = 0
                for i in range(m):
                    for j in range(i + 1, m):
                        pairs += 1
                        mi = methods[i].name
                        mj = methods[j].name
                        if method_field_access.get(mi, set()) & method_field_access.get(mj, set()):
                            shared += 1
                lcom = (pairs - shared) / pairs if pairs > 0 else 0.0

            # RFC: methods in class + distinct methods called by class methods (external)
            called = set()
            for calls in method_calls.values():
                for c in calls:
                    called.add(c)
            # consider internal calls (self.method) as internal if name in method_names
            external_called = set(c for c in called if not ('.' in c and c.split('.')[-1] in method_names) and c not in method_names)
            rfc = len(methods) + len(external_called)

            # NPM: number of public methods
            npm = sum(1 for name in method_names if not name.startswith('_'))

            # TNA: total number of attributes (class + instance)
            tna = len(total_fields)

            # CBO: number of other classes referenced (instantiation, attribute access to other class names, base classes)
            cbo_set = set()
            # bases
            for base in cnode.bases:
                if isinstance(base, ast.Name) and base.id in class_map and base.id != cname:
                    cbo_set.add(base.id)
            # instantiations and attribute accesses in methods
            for calls in method_calls.values():
                for c in calls:
                    # if call looks like OtherClass() or OtherClass.method, check name
                    root = c.split('.')[0]
                    if root in class_map and root != cname:
                        cbo_set.add(root)

            cbo = len(cbo_set)

            # DIT
            dit = inheritance_depth(cnode)

            results.append({
                "name": cname,
                "methods": len(methods),
                "public_methods": npm,
                "wmc": wmc,
                "lcom": round(lcom, 3),
                "rfc": rfc,
                "tna": tna,
                "cbo": cbo,
                "dit": dit,
                "method_field_access": {k: sorted(list(v)) for k, v in method_field_access.items()},
                "method_calls": {k: sorted(list(v)) for k, v in method_calls.items()}
            })

        total_methods = sum(r["methods"] for r in results)

        return {
            "total_classes": len(results),
            "classes": results,
            "total_methods": total_methods,
            "average_methods_per_class": total_methods / len(results),
            "classes_with_inheritance": sum(1 for r in results if r["dit"] > 0),
            "average_inheritance_depth": sum(r["dit"] for r in results) / len(results),
            "average_wmc": sum(r["wmc"] for r in results) / len(results),
            "average_cbo": sum(r["cbo"] for r in results) / len(results),
            "max_wmc": max(r["wmc"] for r in results)
        }

    def _compute_call_graph_metrics(self) -> Dict[str, Any]:
        """Build intra-file call graph and compute depth and density."""
        # collect all functions with qualified names
        funcs = []  # tuples (qualname, node, class_name or None)
        class_of = {}
        if self.tree is None:
            return {
                "nodes": 0,
                "edges": 0,
                "density": 0.0,
                "max_intra_file_call_depth": 0,
                "depths": [],
                "fan_in": {},
                "fan_out": {},
                "avg_fan_in": 0,
                "avg_fan_out": 0,
                "cross_module_calls": {},
                "modules_called": []
            }
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        q = f"{node.name}.{item.name}"
                        funcs.append((q, item, node.name))
                        class_of[q] = node.name
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.append((node.name, node, None))

        name_to_node = {q: n for q, n, _ in funcs}
        names = list(name_to_node.keys())
        edges = defaultdict(set)

        # helper: resolve call name to a qualname if possible
        simple_names = set(names)

        # also collect cross-module calls (heuristic: calls like module.func)
        cross_calls = defaultdict(set)

        for qname, node in name_to_node.items():
            calls = self._collect_calls(node)
            for c in calls:
                target = None
                if '.' in c:
                    parts = c.split('.')
                    # self.foo -> same class
                    if parts[0] == 'self':
                        cls = class_of.get(qname)
                        if cls:
                            candidate = f"{cls}.{parts[-1]}"
                            if candidate in simple_names:
                                target = candidate
                    else:
                        candidate = f"{parts[0]}.{parts[-1]}"
                        if candidate in simple_names:
                            target = candidate
                        else:
                            # treat as cross-module call to module
                            cross_calls[qname].add(parts[0])
                else:
                    if c in simple_names:
                        target = c

                if target:
                    edges[qname].add(target)

        N = len(names)
        E = sum(len(s) for s in edges.values())
        density = E / (N * (N - 1)) if N > 1 else 0.0

        # compute fan-in / fan-out
        fan_out = {n: len(edges.get(n, [])) for n in names}
        fan_in = {n: 0 for n in names}
        for vs in edges.values():
            for v in vs:
                if v in fan_in:
                    fan_in[v] += 1

        # compute max depth using DFS with memoization
        memo = {}

        def depth(u, visited=None):
            if visited is None:
                visited = set()
            if u in memo:
                return memo[u]
            visited.add(u)
            maxd = 0
            for v in edges.get(u, []):
                if v in visited:
                    continue
                d = 1 + depth(v, visited)
                maxd = max(maxd, d)
            visited.remove(u)
            memo[u] = maxd
            return maxd

        max_depth = 0
        depths = []
        for n in names:
            d = depth(n, set())
            depths.append(d)
            max_depth = max(max_depth, d)

        # cross-module calls summary
        cross_modules = {k: sorted(list(v)) for k, v in cross_calls.items()}
        modules_called = set(m for v in cross_calls.values() for m in v)

        return {
            "nodes": N,
            "edges": E,
            "density": density,
            "max_intra_file_call_depth": max_depth,
            "depths": depths,
            "fan_in": fan_in,
            "fan_out": fan_out,
            "avg_fan_in": statistics.mean(fan_in.values()) if fan_in else 0,
            "avg_fan_out": statistics.mean(fan_out.values()) if fan_out else 0,
            "cross_module_calls": cross_modules,
            "modules_called": sorted(list(modules_called))
        }

    def _attribute_mutation_outside_constructor(self) -> Dict[str, Any]:
        """Count attribute mutations to self.* outside __init__"""
        mutations = 0
        per_class = defaultdict(int)
        if self.tree is None:
            return {"total_mutations_outside_init": 0, "per_class": {}}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name != '__init__':
                        for n in ast.walk(item):
                            if isinstance(n, (ast.Assign, ast.AugAssign)):
                                targets = getattr(n, 'targets', []) if isinstance(n, ast.Assign) else [n.target]
                                for t in targets:
                                    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == 'self':
                                        mutations += 1
                                        per_class[node.name] += 1
        return {"total_mutations_outside_init": mutations, "per_class": dict(per_class)}

    def _boolean_expression_metrics(self) -> Dict[str, Any]:
        """Compute boolean expression complexity (counts of BoolOp and nesting)."""
        total_bool_ops = 0
        total_bool_terms = 0
        per_function = {}
        if self.tree is None:
            return {"total_bool_ops": 0, "total_bool_terms": 0, "avg_terms_per_bool_op": 0, "per_function": {}}
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                # for functions, calculate BoolOps inside
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cnt_ops = 0
                    cnt_terms = 0
                    for n in ast.walk(node):
                        if isinstance(n, ast.BoolOp):
                            cnt_ops += 1
                            cnt_terms += len(n.values)
                    per_function[node.name] = {"bool_ops": cnt_ops, "bool_terms": cnt_terms}
                    total_bool_ops += cnt_ops
                    total_bool_terms += cnt_terms
        avg_terms_per_op = (total_bool_terms / total_bool_ops) if total_bool_ops else 0
        return {"total_bool_ops": total_bool_ops, "total_bool_terms": total_bool_terms, "avg_terms_per_bool_op": round(avg_terms_per_op, 2), "per_function": per_function}

    def _global_state_usage(self) -> Dict[str, Any]:
        """Count module-level globals and their usage inside functions."""
        module_assigns = set()
        if self.tree is None:
            return {"globals_declared": 0, "global_usages_total": 0, "usage_per_name": {}}
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        module_assigns.add(t.id)
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                module_assigns.add(node.target.id)

        usage_count = 0
        usage_per_name = defaultdict(int)
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for n in ast.walk(node):
                    if isinstance(n, ast.Name) and n.id in module_assigns:
                        usage_count += 1
                        usage_per_name[n.id] += 1
                    if isinstance(n, ast.Global):
                        for name in n.names:
                            usage_per_name[name] += 1
        return {"globals_declared": len(module_assigns), "global_usages_total": usage_count, "usage_per_name": dict(usage_per_name)}

    def _cyclomatic_ratio_and_param_entropy(self) -> Dict[str, Any]:
        """Compute function-level cyclomatic ratio (cc/loc) and parameter name entropy."""
        ratios = []
        entropies = []
        import math
        if self.tree is None:
            return {"max_cyclomatic_ratio": 0.0, "mean_cyclomatic_ratio": 0.0, "mean_param_entropy": 0.0}
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cc = self._compute_cyclomatic_complexity(node)
                loc = getattr(node, 'end_lineno', None)
                if loc is None:
                    # best-effort: count lines by body
                    loc = sum(1 for _ in ast.walk(node))
                else:
                    loc = loc - node.lineno + 1
                ratio = cc / max(1, loc)
                ratios.append(ratio)

                # parameter entropy
                params = [a.arg for a in node.args.args]
                chars = ''.join(params)
                if chars:
                    freq = defaultdict(int)
                    for ch in chars:
                        freq[ch] += 1
                    L = sum(freq.values())
                    ent = -sum((v / L) * math.log2(v / L) for v in freq.values())
                    entropies.append(ent)
        return {"max_cyclomatic_ratio": max(ratios) if ratios else 0.0, "mean_cyclomatic_ratio": (sum(ratios) / len(ratios)) if ratios else 0.0, "mean_param_entropy": (sum(entropies) / len(entropies)) if entropies else 0.0}

    def _abbrev_and_comment_mismatch(self) -> Dict[str, Any]:
        """Compute abbreviation density in identifiers and comment-code semantic mismatch."""
        idents = []
        if self.tree is None:
            return {"abbrev_density": 0.0, "abbrev_examples": [], "comment_code_mismatch_score": 0.0, "todo_fixme_count": 0}
        # collect identifiers
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                idents.append(node.name)
                # params
                idents.extend(a.arg for a in node.args.args)
            elif isinstance(node, ast.ClassDef):
                idents.append(node.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        idents.append(t.id)

        abbrev = [i for i in idents if re.match(r'^[A-Za-z]{1,3}$', i)]
        abbrev_density = len(abbrev) / len(idents) if idents else 0.0

        # comment-code semantic mismatch per function (using docstring or leading comments)
        mismatch_scores = []
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node) or ''
                # collect preceding inline comments
                leading = []
                if hasattr(node, 'lineno'):
                    i = node.lineno - 2
                    while i >= 0:
                        line = self.lines[i].strip()
                        if line.startswith('#'):
                            leading.insert(0, line.lstrip('#').strip())
                            i -= 1
                        else:
                            break
                comment_text = ' '.join([doc] + leading)
                if not comment_text:
                    continue
                comment_tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]+", comment_text.lower()))
                # code tokens: function name, called functions, variable names
                code_tokens = set()
                code_tokens.add(node.name.lower())
                for n in ast.walk(node):
                    if isinstance(n, ast.Call):
                        func = n.func
                        if isinstance(func, ast.Name):
                            code_tokens.add(func.id.lower())
                        elif isinstance(func, ast.Attribute):
                            code_tokens.add(func.attr.lower())
                    if isinstance(n, ast.Name):
                        code_tokens.add(n.id.lower())

                overlap = comment_tokens & code_tokens
                overlap_ratio = len(overlap) / len(comment_tokens) if comment_tokens else 0
                mismatch_scores.append(1 - overlap_ratio)

        overall_mismatch = sum(mismatch_scores) / len(mismatch_scores) if mismatch_scores else 0.0
        return {"abbrev_density": round(abbrev_density, 3), "abbrev_examples": sorted(list(set(abbrev)))[0:20], "comment_code_mismatch_score": round(overall_mismatch, 3), "todo_fixme_count": len(re.findall(r"\bTODO\b|\bFIXME\b", self.content, flags=re.IGNORECASE))}    
    def _get_numerical_summary(self) -> Dict[str, Any]:
        """Generate numerical summary of all metrics."""
        size = self._get_size_metrics()
        structure = self._get_structure_metrics()
        complexity = self._get_complexity_metrics()
        oo_metrics = self._get_object_oriented_metrics()
        doc_metrics = self._get_documentation_metrics()
        imports = self._get_import_analysis()
        call_graph = self._compute_call_graph_metrics()
        attr_mut = self._attribute_mutation_outside_constructor()
        bool_metrics = self._boolean_expression_metrics()
        globals_usage = self._global_state_usage()
        cc_and_entropy = self._cyclomatic_ratio_and_param_entropy()
        abbrev_mismatch = self._abbrev_and_comment_mismatch()
        halstead = self._halstead_metrics()
        style = self._style_metrics()
        tests = self._test_metrics()
        semantic = self._semantic_textual_metrics()
        vcs = self._get_vcs_metrics()

        decision_density = complexity.get("total_control_structures", 0) / max(1, size.get("SLOC", 1))

        # derived function and class indicators
        funcs = self._get_function_metrics()
        total_external_attr = sum(f.get("external_attr_access", 0) for f in funcs)
        total_internal_attr = sum(f.get("internal_attr_access", 0) for f in funcs)
        external_vs_internal_field_access_ratio = round(total_external_attr / max(1, total_internal_attr), 3)
        long_method_indicator = any((f.get("loc", 0) > 75 or f.get("cyclomatic_complexity", 0) > 15) for f in funcs)
        large_parameter_list_indicator = any(f.get("args_count", 0) > 6 for f in funcs)

        # lines per function statistics
        lines_per_function = [f.get("loc", 0) for f in funcs if f.get("loc", 0) > 0]
        max_lines_per_function = max(lines_per_function) if lines_per_function else 0
        mean_lines_per_function = round(statistics.mean(lines_per_function), 2) if lines_per_function else 0.0

        # class-level indicators
        lazy_class_indicator = False
        god_class_proxies = []
        for c in oo_metrics.get("classes", []):
            if c.get("lazy_ratio", 0) > 3:
                lazy_class_indicator = True
            if (c.get("methods", 0) > 20 and c.get("wmc", 0) > 50) or (c.get("tna", 0) > 30 and c.get("methods", 0) > 15):
                god_class_proxies.append({"name": c.get("name"), "methods": c.get("methods"), "wmc": c.get("wmc"), "tna": c.get("tna")})

        # lines per class statistics
        lines_per_class = [c.get("line_count", 0) for c in oo_metrics.get("classes", []) if c.get("line_count", 0) > 0]
        max_lines_per_class = max(lines_per_class) if lines_per_class else 0
        mean_lines_per_class = round(statistics.mean(lines_per_class), 2) if lines_per_class else 0.0

        # inter-file coupling and cross-file call edges (heuristic)
        inter_file_coupling = len(call_graph.get("modules_called", []))
        cross_file_call_edges = []
        for caller, modules in call_graph.get("cross_module_calls", {}).items():
            for m in modules:
                cross_file_call_edges.append({"caller": caller, "module": m})

        pep8 = self._pep8_violations()
        indent = self._indentation_irregularity()
        todo_fixme_semantic_density = semantic.get("todo_density", 0)

        # VCS-derived fields (best-effort)
        lines_added = vcs.get("lines_added") if isinstance(vcs, dict) else None
        lines_deleted = vcs.get("lines_deleted") if isinstance(vcs, dict) else None
        num_authors = vcs.get("num_authors") if isinstance(vcs, dict) else None
        file_age = vcs.get("file_age_days") if isinstance(vcs, dict) else None
        commit_bursts = vcs.get("commit_bursts") if isinstance(vcs, dict) else None
        coupled_file_changes = vcs.get("coupled_file_changes") if isinstance(vcs, dict) else None

        # embeddings and docstring topics removed per request
        halstead_difficulty = halstead.get("difficulty", 0)
        halstead_estimated_bugs = halstead.get("estimated_bugs", 0)

        return {
            "file_path": self.filepath,
            "lines_of_code": size["LOC"],
            "source_lines": size["SLOC"],
            "comment_lines": size["CLOC"],
            "comment_percentage": round(size["comment_density"] * 100, 1),
            "classes": structure["classes"],
            "functions": structure["functions"],
            "methods": oo_metrics.get("total_methods", 0),
            "average_cyclomatic_complexity": round(complexity["average_cyclomatic_per_function"], 2),
            "max_nesting_level": complexity["max_nesting_level"],
            "nesting_variance": complexity.get("nesting_variance", 0),
            "decision_density": round(decision_density, 4),
            "boolean_expression_avg_terms": bool_metrics.get("avg_terms_per_bool_op", 0),
            "max_intra_file_call_depth": call_graph.get("max_intra_file_call_depth", 0),
            "call_graph_density": round(call_graph.get("density", 0), 4),
            "inter_file_coupling": inter_file_coupling,
            "cross_file_call_edges": cross_file_call_edges,
            "attribute_mutations_outside_init": attr_mut.get("total_mutations_outside_init", 0),
            "external_vs_internal_field_access_ratio": external_vs_internal_field_access_ratio,
            "max_lines_per_function": max_lines_per_function,
            "mean_lines_per_function": mean_lines_per_function,
            "max_lines_per_class": max_lines_per_class,
            "mean_lines_per_class": mean_lines_per_class,
            "globals_declared": globals_usage.get("globals_declared", 0),
            "global_usages_total": globals_usage.get("global_usages_total", 0),
            "max_cyclomatic_ratio": round(cc_and_entropy.get("max_cyclomatic_ratio", 0), 3),
            "mean_cyclomatic_ratio": round(cc_and_entropy.get("mean_cyclomatic_ratio", 0), 3),
            "mean_param_entropy": round(cc_and_entropy.get("mean_param_entropy", 0), 3),
            "abbreviation_density": abbrev_mismatch.get("abbrev_density", 0),
            "comment_code_mismatch_score": abbrev_mismatch.get("comment_code_mismatch_score", 0),
            "todo_fixme_count": abbrev_mismatch.get("todo_fixme_count", 0),
            "todo_fixme_semantic_density": todo_fixme_semantic_density,
            "halstead_volume": round(halstead.get("volume", 0), 2),
            "halstead_effort": round(halstead.get("effort", 0), 2),
            "halstead_difficulty": halstead_difficulty,
            "halstead_estimated_bugs": halstead_estimated_bugs,
            "avg_line_length": round(style.get("avg_line_length", 0), 1),
            "max_line_length": style.get("max_line_length", 0),
            "percent_lines_over_80": round(style.get("percent_lines_over_80", 0), 3),
            "pep8_violations": pep8.get("count") if isinstance(pep8, dict) else None,
            "pep8_examples": pep8.get("examples") if isinstance(pep8, dict) else None,
            "indentation_irregularity": indent,
            "test_files_found": tests.get("test_files_found", 0),
            "test_lines": tests.get("test_lines", 0),
            "test_function_count": tests.get("test_function_count", 0),
            "unit_test_presence": tests.get("unit_test_presence", False),
            "test_to_source_ratio": round(tests.get("test_lines", 0) / max(1, size.get("SLOC", 1)), 3),
            "semantic_todo_density": semantic.get("todo_density", 0),
            "todo_fixme_semantic_density": todo_fixme_semantic_density,
            "vcs_available": vcs.get("repo_available", False) if isinstance(vcs, dict) else False,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "num_authors": num_authors,
            "file_age_days": file_age,
            "commit_bursts": commit_bursts,
            "coupled_file_changes": coupled_file_changes,
            "vcs_top_coupled": vcs.get("top_coupled_files") if isinstance(vcs, dict) else None,
            "average_methods_per_class": round(oo_metrics.get("average_methods_per_class", 0), 2),
            "classes_with_inheritance": oo_metrics.get("classes_with_inheritance", 0),
            "lazy_class_indicator": lazy_class_indicator,
            "god_class_proxies": god_class_proxies,
            "long_method_indicator": long_method_indicator,
            "large_parameter_list_indicator": large_parameter_list_indicator,
            "documentation_coverage": round(doc_metrics["documentation_coverage"] * 100, 1),
            "total_imports": imports["total_imports"],
            "maintainability_score": self._calculate_maintainability_score()
        }
    
    def _semantic_textual_metrics(self) -> Dict[str, Any]:
        """Extract semantic and textual metrics."""
        todo_count = len(re.findall(r"\bTODO\b", self.content, flags=re.IGNORECASE))
        fixme_count = len(re.findall(r"\bFIXME\b", self.content, flags=re.IGNORECASE))
        total_todos = todo_count + fixme_count
        
        todo_density = total_todos / max(1, len(self.lines))
        
        return {
            "todo_count": todo_count,
            "fixme_count": fixme_count,
            "total_semantic_issues": total_todos,
            "todo_density": round(todo_density, 4)
        }

    # hashed embedding helper removed to keep analyzer lightweight and avoid storing embeddings.
    # If embeddings are needed later, implement a deterministic, dependency-free method here.


    def _pep8_violations(self) -> Dict[str, Any]:
        """Try running pycodestyle if available, otherwise use heuristics to approximate PEP8 violations."""
        issues = []
        try:
            proc = subprocess.run(["pycodestyle", "--max-line-length=79", self.filepath], capture_output=True, text=True, timeout=5)
            out = proc.stdout.strip()
            if out:
                lines = out.splitlines()
                for l in lines[:500]:
                    issues.append(l.strip())
            return {"count": len(issues), "examples": issues[:20], "used_tool": True}
        except Exception:
            examples = []
            count = 0
            for i, line in enumerate(self.lines):
                if len(line) > 79:
                    count += 1
                    if len(examples) < 20:
                        examples.append(f"line {i+1}: length {len(line)}")
                if line.rstrip() != line and len(examples) < 20:
                    count += 1
                    examples.append(f"line {i+1}: trailing whitespace")
            return {"count": count, "examples": examples[:20], "used_tool": False}

    # docstring topic modeling removed per request. If needed, add a lightweight token-frequency extractor here.

    def _indentation_irregularity(self) -> Dict[str, Any]:
        """Measure indentation irregularity (tabs vs spaces and variance in indent sizes)."""
        indents = []
        tab_lines = 0
        mixed_tabs = 0
        for line in self.lines:
            if not line.strip():
                continue
            match = re.match(r'^[ \t]*', line)
            if not match:
                continue
            leading = match.group(0)
            if '\t' in leading:
                tab_lines += 1
            if ' ' in leading and '\t' in leading:
                mixed_tabs += 1
            spaces = leading.replace('\t', ' ' * 4)
            indents.append(len(spaces))
        if not indents:
            return {"irregularity_score": 0.0, "tab_lines": tab_lines, "mixed_tabs": mixed_tabs}
        mean = statistics.mean(indents)
        stdev = statistics.pstdev(indents)
        irregularity = stdev / mean if mean > 0 else 0
        return {"irregularity_score": round(irregularity, 4), "tab_lines": tab_lines, "mixed_tabs": mixed_tabs, "indent_stddev": round(stdev, 2)}

    def _halstead_metrics(self) -> Dict[str, Any]:
        """Calculate Halstead metrics (volume, effort, etc.)."""
        operators = set()
        operands = set()
        
        if self.tree is None:
            return {"volume": 0, "effort": 0, "difficulty": 0, "estimated_bugs": 0}
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.BinOp):
                operators.add(type(node.op).__name__)
            elif isinstance(node, ast.Name):
                operands.add(node.id)
            elif isinstance(node, ast.Constant):
                operands.add(str(node.value))
        
        n1 = len(operators)
        n2 = len(operands)
        N1 = sum(1 for node in ast.walk(self.tree) if isinstance(node, ast.BinOp))
        N2 = sum(1 for node in ast.walk(self.tree) if isinstance(node, ast.Name) or isinstance(node, ast.Constant))
        
        if n1 == 0 or n2 == 0:
            return {"volume": 0, "effort": 0, "difficulty": 0, "estimated_bugs": 0}
        
        N = N1 + N2
        volume = N * math.log2(n1 + n2) if (n1 + n2) > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume
        estimated_bugs = volume / 3000 if volume > 0 else 0
        
        return {
            "volume": round(volume, 2),
            "effort": round(effort, 2),
            "difficulty": round(difficulty, 2),
            "n1_operators": n1,
            "n2_operands": n2,
            "estimated_bugs": round(estimated_bugs, 4)
        }
    
    def _style_metrics(self) -> Dict[str, Any]:
        """Analyze code style metrics (line length, indentation, etc.)."""
        line_lengths = [len(line) for line in self.lines]
        
        if not line_lengths:
            return {
                "avg_line_length": 0,
                "max_line_length": 0,
                "percent_lines_over_80": 0
            }
        
        avg_length = sum(line_lengths) / len(line_lengths)
        max_length = max(line_lengths)
        over_80 = sum(1 for length in line_lengths if length > 80)
        percent_over_80 = (over_80 / len(line_lengths)) * 100 if line_lengths else 0
        
        return {
            "avg_line_length": round(avg_length, 1),
            "max_line_length": max_length,
            "percent_lines_over_80": round(percent_over_80, 2)
        }
    
    def _test_metrics(self) -> Dict[str, Any]:
        """Analyze test coverage and test file metrics."""
        test_files_found = 0
        test_lines = 0
        test_function_count = 0
        unit_test_presence = False

        # Look for test files in the same directory or parent directories
        try:
            current_dir = os.path.dirname(self.filepath)
            for root, _, files in os.walk(current_dir):
                for file in files:
                    if (file.startswith('test_') or file.endswith('_test.py')) and file.endswith('.py'):
                        test_files_found += 1
                        test_file_path = os.path.join(root, file)
                        try:
                            with open(test_file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                lines = content.splitlines()
                                test_lines += len(lines)
                                test_function_count += sum(1 for l in lines if re.match(r"\s*def\s+test_", l))
                                # presence heuristic: same module name in test filename
                                base = os.path.splitext(os.path.basename(self.filepath))[0]
                                if base in os.path.splitext(file)[0]:
                                    unit_test_presence = True
                        except Exception:
                            pass
        except Exception:
            pass

        return {
            "test_files_found": test_files_found,
            "test_lines": test_lines,
            "test_function_count": test_function_count,
            "unit_test_presence": unit_test_presence
        }

    def _get_vcs_metrics(self) -> Dict[str, Any]:
        """Extract version control system metrics (best-effort using git).

        Returns keys: repo_available, NR, lines_added, lines_deleted, num_authors,
        file_age_days, commit_bursts, coupled_file_changes (dict), top_coupled_files (list), commit_messages.
        """
        try:
            file_dir = os.path.dirname(self.filepath) or '.'
            proc = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=file_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if proc.returncode != 0 or not proc.stdout.strip():
                return {"repo_available": False}
            repo_root = proc.stdout.strip()

            cmd = ["git", "log", "--pretty=format:%H|%an|%ad|%s", "--date=iso", "--numstat", "--", self.filepath]
            proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, timeout=10)
            if proc.returncode != 0:
                return {"repo_available": False}

            out = proc.stdout.splitlines()
            commits = []
            i = 0
            while i < len(out):
                line = out[i]
                if '|' in line:
                    parts = line.split('|', 3)
                    if len(parts) < 4:
                        i += 1
                        continue
                    chash, author, adate, subject = parts
                    adate_dt = None
                    try:
                        adate_dt = datetime.fromisoformat(adate.strip())
                    except Exception:
                        try:
                            adate_dt = datetime.strptime(adate.strip(), "%Y-%m-%d %H:%M:%S %z")
                        except Exception:
                            adate_dt = None
                    i += 1
                    added = 0
                    deleted = 0
                    other_files = set()
                    while i < len(out) and out[i].strip() and '|' not in out[i]:
                        ns = out[i].split('\t')
                        if len(ns) >= 3:
                            a_str, d_str, fname = ns[0], ns[1], ns[2]
                            try:
                                a = int(a_str) if a_str != '-' else 0
                                d = int(d_str) if d_str != '-' else 0
                            except Exception:
                                a = d = 0
                            file_path = fname.strip()
                            # co-changed files
                            try:
                                abs_target = os.path.abspath(self.filepath)
                                abs_file = os.path.abspath(os.path.join(repo_root, file_path))
                                if abs_file != abs_target:
                                    other_files.add(file_path)
                                else:
                                    added += a
                                    deleted += d
                            except Exception:
                                # fallback: if path equals basename
                                if os.path.basename(file_path) == os.path.basename(self.filepath):
                                    try:
                                        added += int(a_str) if a_str != '-' else 0
                                        deleted += int(d_str) if d_str != '-' else 0
                                    except Exception:
                                        pass
                        i += 1
                    commits.append({"hash": chash, "author": author, "date": adate_dt, "subject": subject, "added": added, "deleted": deleted, "co_changed": other_files})
                else:
                    i += 1

            if not commits:
                return {"repo_available": True, "NR": 0, "lines_added": 0, "lines_deleted": 0, "num_authors": 0, "file_age_days": 0, "commit_bursts": 0, "coupled_file_changes": {}, "top_coupled_files": []}

            total_added = sum(c["added"] for c in commits)
            total_deleted = sum(c["deleted"] for c in commits)
            authors = set(c["author"] for c in commits if c.get("author"))

            dates = [c["date"] for c in commits if c["date"] is not None]
            file_age_days = 0
            if dates:
                earliest = min(dates)
                latest = max(dates)
                file_age_days = max(0, (latest - earliest).days)

            # commit bursts: max commits in any 7-day window
            dates_sorted = sorted(dates)
            max_in_window = 0
            for idx, d in enumerate(dates_sorted):
                count = 1
                j = idx + 1
                while j < len(dates_sorted) and (dates_sorted[j] - d).days <= 7:
                    count += 1
                    j += 1
                max_in_window = max(max_in_window, count)

            cochange_counts = defaultdict(int)
            for c in commits:
                for f in c["co_changed"]:
                    cochange_counts[f] += 1
            top_coupled = sorted(cochange_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_coupled_list = [{"file": k, "count": v} for k, v in top_coupled]

            return {
                "repo_available": True,
                "NR": len(commits),
                "lines_added": total_added,
                "lines_deleted": total_deleted,
                "num_authors": len(authors),
                "file_age_days": file_age_days,
                "commit_bursts": max_in_window,
                "coupled_file_changes": dict(cochange_counts),
                "top_coupled_files": top_coupled_list,
                "commit_messages": [c["subject"] for c in commits if c.get("subject")]
            }
        except Exception:
            return {"repo_available": False}

    def _calculate_maintainability_score(self) -> float:
        """Calculate a simple maintainability score (0-100)."""
        score = 100
        
        # Adjust based on various factors
        size = self._get_size_metrics()
        complexity = self._get_complexity_metrics()
        doc_metrics = self._get_documentation_metrics()
        
        # Size penalty
        if size["LOC"] > 200:
            score -= 20
        elif size["LOC"] > 100:
            score -= 10
        
        # Complexity penalty
        if complexity["estimated_cyclomatic_complexity"] > 20:
            score -= 20
        elif complexity["estimated_cyclomatic_complexity"] > 10:
            score -= 10
        
        # Documentation bonus/penalty
        if doc_metrics["documentation_coverage"] > 0.8:
            score += 10
        elif doc_metrics["documentation_coverage"] < 0.3:
            score -= 15
        
        return max(0, min(100, round(score, 1)))
