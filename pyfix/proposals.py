"""Transparent single-location AST edits. No clean source or labels from the corpus.
Candidate enumeration is a bounded search, not a learned repair model.
"""
import ast
import copy

LABELS=('type_conversion','missing_none_guard','index_boundary','missing_mapping_key','zero_denominator','wrong_argument_count')

def candidates(source,label):
    tree=ast.parse(source);out=[];seen={ast.unparse(tree)}
    def emit(target,replacement,reason):
        class Replace(ast.NodeTransformer):
            def visit(self,node):
                if node is target:return copy.deepcopy(replacement)
                return super().visit(node)
        # Restore by re-parsing for every proposal: target belongs to the original tree.
        candidate=Replace().visit(copy.copy(tree))
        # Transformer may change descendants, so the immutable source is restored below by caller.
        text=ast.unparse(ast.fix_missing_locations(candidate))+'\n'
        if text.strip() not in seen:
            seen.add(text.strip());out.append({'source':text,'reason':reason,'strategy':label})
    # Each iteration reconstructs the tree to avoid accumulating unrelated edits.
    plans=[]
    for index,node in enumerate(ast.walk(tree)):
        expr=lambda value:ast.parse(value,mode='eval').body
        if label=='type_conversion':
            targets=[]
            if isinstance(node,ast.BinOp):
                if isinstance(node.left,(ast.Name,ast.Subscript)): targets.append(('left',node.left))
                if isinstance(node.right,(ast.Name,ast.Subscript)): targets.append(('right',node.right))
            if isinstance(node,ast.AugAssign): targets.append(('value',node.value))
            if isinstance(node,ast.GeneratorExp):targets.append(('elt',node.elt))
            for field,value in targets:
                for cast in ['float','int']:
                    replacement=copy.deepcopy(node);setattr(replacement,field,expr(f'{cast}({ast.unparse(value)})'))
                    plans.append((index,replacement,f'Convert {ast.unparse(value)} with {cast} at the arithmetic boundary.'))
        elif label=='missing_none_guard':
            targets=[]
            if isinstance(node,ast.Assign) and isinstance(node.value,ast.Name):targets.append(('value',node.value))
            if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name):targets.append(('value',node.value))
            for field,value in targets:
                for default in ['[]','""','{}']:
                    replacement=copy.deepcopy(node);name=ast.unparse(value)
                    setattr(replacement,field,expr(f'({name} if {name} is not None else {default})'))
                    plans.append((index,replacement,f'Handle None explicitly with {default}; preserve other falsy values.'))
        elif label=='index_boundary':
            if isinstance(node,ast.Subscript) and not isinstance(node.slice,ast.Slice):
                replacement=copy.deepcopy(node);replacement.slice=expr(f'({ast.unparse(node.slice)}) - 1')
                plans.append((index,replacement,'Move the element index inside the upper boundary.'))
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='range' and node.args:
                arg=0 if len(node.args)==1 else 1
                replacement=copy.deepcopy(node);replacement.args[arg]=expr(f'({ast.unparse(node.args[arg])}) - 1')
                plans.append((index,replacement,'Reduce the exclusive iteration bound by one.'))
        elif label=='missing_mapping_key':
            if isinstance(node,ast.Subscript) and isinstance(node.slice,ast.Constant) and isinstance(node.slice.value,str):
                for default in ['0','""','"guest"','"en"']:
                    replacement=expr(f'{ast.unparse(node.value)}.get({ast.unparse(node.slice)}, {default})')
                    plans.append((index,replacement,f'Use an optional key lookup with candidate default {default}; tests must establish the contract.'))
        elif label=='zero_denominator':
            if isinstance(node,ast.If) and isinstance(node.test,ast.Constant) and node.test.value is False:
                for division in ast.walk(tree):
                    if isinstance(division,ast.BinOp) and isinstance(division.op,(ast.Div,ast.FloorDiv,ast.Mod)):
                        replacement=copy.deepcopy(node);replacement.test=expr(f'{ast.unparse(division.right)} == 0')
                        plans.append((index,replacement,'Restore the existing zero-denominator fallback branch.'))
        elif label=='wrong_argument_count':
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                name=node.func.id
                arities={'abs':1,'len':1,'pow':2,'divmod':2}
                arities.update({n.name:len(n.args.args) for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)})
                if name in arities:
                    needed=arities[name]
                    if len(node.args)>needed:
                        replacement=copy.deepcopy(node);replacement.args=replacement.args[:needed]
                        plans.append((index,replacement,'Remove excess positional arguments to match the callable signature.'))
                    if len(node.args)<needed:
                        for value in ['2','3','0','1','10','"ID-"']:
                            replacement=copy.deepcopy(node);replacement.args+= [expr(value) for _ in range(needed-len(node.args))]
                            plans.append((index,replacement,'Supply candidate missing arguments; verify their semantics with tests.'))
                            if len(node.args)==1 and needed==2:
                                replacement=copy.deepcopy(node);replacement.args=[expr(value),*replacement.args]
                                plans.append((index,replacement,'Supply a candidate leading argument and preserve the existing argument.'))
    for index,replacement,reason in plans:
        tree=ast.parse(source)
        target=list(ast.walk(tree))[index]
        emit(target,replacement,reason)
    return out

def ordered_candidates(source,label,guided=True):
    strategies=[label] if guided else list(LABELS)
    return [candidate for strategy in strategies for candidate in candidates(source,strategy)]
