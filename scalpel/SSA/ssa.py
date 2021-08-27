""" 
In this module, the single static assignment forms are  implemented to allow
futher anaysis. The module contain a single class named SSA.
"""
import ast
import astor
from functools import reduce
from collections import OrderedDict
import networkx as nx
from ..core.vars_visitor import get_vars
from ..cfg.builder import CFGBuilder, Block, invert
from ..core.mnode import MNode
from ..core.vars_visitor  import get_vars

BUILT_IN_FUNCTIONS = set([ 
         ### built-in functions
        "abs","delattr", "print", "str", "bin", "int", "xrange", "eval", "all", "__name__",
        "float", "open", "unicode", "exec",
        "hash","memoryview","set", "tuple", "range", "self" "all","dict","help","min","setattr","any","dir","hex","next","slice", "self",
        "ascii","divmod","enumerate","id", "isinstance", "object","sorted","bin","enumerate","input",
        "staticmethod","bool", "eval" "int", "len", "self", "open" "str" "breakpoint" "exec" "isinstance" "ord",
        "sum", "bytearray", "filter", "issubclass", "pow", "super", "bytes", "float", "iter", "print"
        "tuple", "callable", "format", "len", "property", "type", "chr","frozenset", "list", "range", "vars", 
        "classmethod", "getattr", "locals", "repr", "repr", "zip", "compile", "globals", "map", "reversed",  "__import__", "complex", "hasattr", "max", "round", "get_ipython",
        "ord",
        ###  built-in exceptions

        "BaseException", "SystemExit", "KeyboardInterrupt", "GeneratorExit", "Exception",
        "StopIteration", "StopAsyncIteration","ArithmeticError", "FloatingPointError", "OverflowError",
        "ZeroDivisionError","AssertionError", "AttributeError", "BufferError", "EOFError",
        "ImportError", "ModuleNotFoundError", "LookupError", "IndexError" , "KeyError", "MemoryError", "NameError",
        "UnboundLocalError", "OSError", "IOError", "BlockingIOError", "ChildProcessError", "ConnectionError",
        "BrokenPipeError", "ConnectionAbortedError", "ConnectionRefusedError","ConnectionResetError",
        "FileExistsError", "FileNotFoundError", "InterruptedError","IsADirectoryError", "NotADirectoryError",
        "PermissionError","ProcessLookupError", "TimeoutError", "ReferenceError", "RuntimeError",
        "NotImplementedError","RecursionError", "SyntaxError", "IndentationError", "TabError",
        "SystemError", "TypeError", "ValueError","UnicodeError","UnicodeDecodeError","UnicodeEncodeError","UnicodeTranslateError",
        # built-in warnings
        "Warning","DeprecationWarning","PendingDeprecationWarning","RuntimeWarning","SyntaxWarning",
        "UserWarning", "FutureWarning","ImportWarning","UnicodeWarning","BytesWarning","ResourceWarning",
        # Others
        "NotImplemented", "__main__", "__file__", "__name__", "__debug__"
        ]
        )

def parse_val(node):
   # does not return anything
   if isinstance(node, ast.Constant):
       return node.value
   if isinstance(node, ast.Str):
       if hasattr(node, "value"):
           return node.value
       else:
           return node.s
   return "other"

class SSA:
    """
    Build SSA graph from a given AST node based on the CFG.
    """
    def __init__ (self, src):
        """
        Args:
            src: the source code as input.
        """
        # the class SSA takes a module as the input 
        self.src = src   # source code
        self.module_ast = ast.parse(src)
        self.numbering = {}  # numbering variables
        self.var_values = {}  # numbering variables
        self.m_node = MNode("tmp")
        self.m_node.source = self.src
        self.m_node.gen_ast() 
        self.global_live_idents = []
        self.ssa_blocks = []
        self.error_paths = {}
        self.dom = {}

        self.block_ident_gen = {}
        self.block_ident_use = {}
        self.reachable_table = {}
        id2block = {}
        self.unreachable_names = {}
        self.undefined_names_from = {}

    def get_global_live_vars(self):
        #import_dict = self.m_node.parse_import_stmts()
        #def_records = self.m_node.parse_func_defs()
        #def_idents = [r['name'] for r in def_records if r['scope'] == 'mod']
        #self.global_live_idents = def_idents + list(import_dict.keys())
        self.global_live_idents = []

    def flatten_tuple(ast_tuple):
        """
        input: ast tuple object
        return a list of elements in the given tuple
        """
        output =[]
        first = ast_tuple[0]
        second = ast_tuple[1]  


    def get_assign_raw(self, stmts):
        """
        Retrieve the assignment statements 
        Args:
            stmts: A list of statements from the block node in the CFG.
        """
        assign_stmts = []
        for stmt in stmts:
            if isinstance(stmt,ast.Assign):
                if isinstance(stmt.targets, list):
                    for target in stmt.targets:
                        if hasattr(target, "id"):
                            assign_stmts.append((target, stmt.value))
                        elif isinstance(target, ast.Tuple):
                            for elt in target.elts:
                                if hasattr(elt, "id"):
                                    assign_stmts.append((elt, stmt.value))

            elif isinstance(stmt,ast.AnnAssign):
                if hasattr(stmt.target, "id"):
                    assign_stmts.append((stmt.target, stmt.value))
            elif isinstance(stmt, ast.AugAssign):
                if hasattr(stmt.target, "id"):
                    assign_stmts.append((stmt.target, stmt.value))
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                if isinstance(stmt.value.func, ast.Attribute):
                    assign_stmts.append((None, stmt.value  ))
                else:
                    assign_stmts.append((None, stmt.value  ))
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value,
                    ast.Attribute):
                assign_stmts.append((None,  stmt))
            elif isinstance(stmt, ast.For):
                if isinstance(stmt.target, ast.Name):
                    assign_stmts.append((stmt.target,  stmt.iter))
                elif isinstance(stmt.target, ast.Tuple):
                    for item in stmt.target.elts:
                        if isinstance(item, ast.Tuple):
                            for elt in item.elts:
                                assign_stmts.append((elt,  stmt.iter))
                        else:
                            assign_stmts.append((item,  stmt.iter))
            elif isinstance(stmt, ast.Import):
                for name in stmt.names:
                    if name.asname is not None:
                        assign_stmts.append((ast.Name(name.asname, ast.Store()),  None))
                    else:
                        assign_stmts.append((ast.Name(name.name, ast.Store()),  None))
            elif isinstance(stmt, ast.ImportFrom):
                print(ast.dump(stmt))
                for name in stmt.names:
                    if name.asname is not None:
                        assign_stmts.append((ast.Name(name.asname, ast.Store()),  None))
                    else:
                        assign_stmts.append((ast.Name(name.name, ast.Store()),  None))
            elif isinstance(stmt, ast.Return):
                    assign_stmts.append((None,  stmt.value))
            elif isinstance(stmt, ast.FunctionDef):
                    assign_stmts.append((ast.Name(stmt.name, ast.Store()),  None))
            elif isinstance(stmt, ast.ClassDef):
                    assign_stmts.append((ast.Name(stmt.name, ast.Store()),  None))
            elif isinstance(stmt, ast.With):
                    for item in stmt.items:
                        # left: optional_vars  right: context_expr
                        assign_stmts.append((item.optional_vars, item.context_expr))

        return assign_stmts

    def get_attribute_stmts(self, stmts):
        call_stmts = []
        for stmt in stmts:
            if isinstance(stmt,ast.Call) and isinstance(stmt.func, ast.Attribute):
                call_stmts += [stmt]

    def get_identifiers(self, ast_node):
        """
        Extract all identifiers from the given AST node.
        Args:
            ast_node: AST node.
        """
        if ast_node is None:
            return []
        res = get_vars(ast_node)
        idents = [r['name'] for r in res if  r['name'] is not None and "." not in r['name']]
        return idents


    def backward_query(self, block, ident_name, visited, path = []):
        phi_fun = []
        visited.add(block.id)
        path.append(block.id)
        # all the incoming path
        for suc_link in block.predecessors: 
            is_this_path_done = False 
            parent_block = suc_link.source
            target_block = suc_link.target
            # deal with cycles, this is back edge
            if parent_block is None:
                continue
            if parent_block.id in visited or parent_block.id == block.id:
                continue

            # if the block dominates the parent block, then give it up
            if parent_block.id in self.dom and  block.id in self.dom[parent_block.id]:
                continue

            #grand_parent_blocks = [link.source for link in parent_block.predecessors]
            #grand_parent_block_ids = [b.id for b in grand_parent_blocks]
            #if block.id in grand_parent_block_ids:
            #    continue
            #if ident_name == 'condition':
                #print('testing')
                #self.print_block(parent_block)
            target_ssa_left = reversed(list(parent_block.ssa_form.keys())) 
            block_phi_fun = []
            for tmp_var_no in target_ssa_left:
                if tmp_var_no[0] == ident_name:
                    block_phi_fun.append(tmp_var_no) 
                    is_this_path_done = True
                    break
            # this is one block 
            #phi_fun += block_phi_fun
            if is_this_path_done:
                phi_fun += block_phi_fun
                continue
            if len(block_phi_fun) == 0:
                # not found in this parent_block
                if len(parent_block.predecessors)!=0 and parent_block.id not in visited:
                    block_phi_fun = self.backward_query(parent_block,
                            ident_name, visited, path = path)
                    #phi_fun += block_phi_fun
            #else:
            #    phi_fun += block_phi_fun
            if len(block_phi_fun) == 0:
                phi_fun += [(ident_name, -1)]
                if ident_name in self.error_paths:
                    self.error_paths[ident_name].append(path.copy())
                else:
                    self.error_paths[ident_name] = [path.copy()]
            else:
                phi_fun += block_phi_fun
        path.pop()
        return phi_fun

    def get_stmt_idents_ctx(self, stmt):
        # if this is a definition of class/function, ignore
        stored_idents = []
        loaded_idents = []
        func_names = []
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # todo, values to named params
            stored_idents.append(stmt.name)
            func_names.append(stmt.name)
            return stored_idents, loaded_idents, func_names

        # if this is control flow statements, we should not visit its body to avoid duplicates
        # as they are already in the next blocks

        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            for alias in stmt.names:
                if alias.asname is None:
                    stored_idents += [alias.name.split('.')[0]]
                else:
                    stored_idents += [alias.asname.split('.')[0]]
            return stored_idents, loaded_idents, []

        if isinstance(stmt, (ast.Try)):
            for handler in stmt.handlers:
                if handler.name is not None:
                    stored_idents.append(handler.name)
            return stored_idents, loaded_idents, []

        visit_node = stmt
        if isinstance(visit_node,(ast.If, ast.IfExp)):
            #visit_node.body = []
            #visit_node.orlse=[]
            visit_node = stmt.test

        if isinstance(visit_node,(ast.With)):
            visit_node.body = []
            visit_node.orlse=[]

        if isinstance(visit_node,(ast.While)):
            visit_node.body = []
        if isinstance(visit_node,(ast.For)):
            visit_node.body = []

        ident_info = get_vars(visit_node)
        for r in ident_info:
            if r['name'] is None or "." in r['name']:
                continue
            if r['usage'] == 'store':
                stored_idents.append(r['name'])
            else:
                loaded_idents.append(r['name'])
        return stored_idents, loaded_idents, []

    def compute_undefined_names(self, cfg, scope=["mod"]):
        """
        generate undefined names from given cfg
        """
        all_blocks = cfg.get_all_blocks()
        reachable_table = {}
        id2block = {}
        block_ident_gen = {}
        block_ident_use = {}
        block_ident_unorder = {}

        subscope_undefined_names = []
        undefined_names_table = [] 
        undefined_names = []

        dom = self.compute_dom_old(all_blocks) 
        idom = self.compute_idom(all_blocks)
    

        for block in all_blocks:
            #assign_records = self.get_assign_raw(block.statements)
            id2block[block.id] = block
            block_ident_gen[block.id] = []
            block_ident_use[block.id] = []
            block_ident_unorder[block.id] = []
            ident_to_be_traced = []
            for stmt in block.statements:
                stored_idents, loaded_idents, scope_func_names = self.get_stmt_idents_ctx(stmt) 
                for ident in loaded_idents:
                    # cannot find in previous statements or current statements
                    # we cannot load values from stored one in one statement 
                    # a = a+2 
                    # in the case x = [i+1 for i in range(10)]
                    if ident not in block_ident_gen[block.id] and ident not in stored_idents:
                                ident_to_be_traced.append((ident, ".".join(scope)))
                    #if ident not in block_ident_gen[block.id]:
                    #    if isinstance(stmt, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                    #        ident_to_be_traced.append(ident)
                    #    else:
                    #        if ident not in stored_idents:
                    #            ident_to_be_traced.append(ident) 
                block_ident_gen[block.id] += stored_idents
                block_ident_unorder[block.id]  += scope_func_names
            block_ident_use[block.id]  = ident_to_be_traced 

        for block in all_blocks:
            # number of stmts parsed
            for stmt in block.statements:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):

                    fun_undefined_names = self.compute_undefined_names(cfg.functioncfgs[(block.id, stmt.name)], scope = scope+[stmt.name])  
                    fun_args = cfg.function_args[(block.id, stmt.name)]
                    # exclude arguments 
                    #fun_undefined_names = [name for name in fun_undefined_names if name not in tmp_avail_names] 
                    fun_idx = block_ident_gen[block.id].index(stmt.name)
                    part_ident_gen = block_ident_gen[block.id][0:fun_idx]
                    # arguments its own name + part of gen set and unorder func/class/def names
                    tmp_avail_names = fun_args + [stmt.name] + block_ident_unorder[block.id] +part_ident_gen
                    fun_undefined_names = [name for name in fun_undefined_names if name[0] not in tmp_avail_names]
                    subscope_undefined_names += fun_undefined_names

                elif isinstance(stmt, ast.ClassDef):
                    class_cfg = cfg.class_cfgs[stmt.name]
                    cls_body_undefined_names = self.compute_undefined_names(class_cfg, scope = scope+[stmt.name])
                    cls_idx = block_ident_gen[block.id].index(stmt.name)
                    part_ident_gen = block_ident_gen[block.id][0:cls_idx] 

                    tmp_avail_names = part_ident_gen + [stmt.name] + block_ident_unorder[block.id]
                    cls_body_undefined_names = [name for name in cls_body_undefined_names if name[0] not in tmp_avail_names]
                    subscope_undefined_names += cls_body_undefined_names
            #subscope_undefined_names = [name for name in subscope_undefined_names if name not in block_ident_gen[block.id]]
            # process this block
            block_id = block.id
            all_used_idents = block_ident_use[block_id]+ list(set(subscope_undefined_names)) 
            #all_used_idents = []
            idents_non_local = [ident for ident in all_used_idents if ident[0] not in BUILT_IN_FUNCTIONS]
            idents_non_local = list(set(idents_non_local))
            idents_left = []
            dominators = dom[block_id]

            for ident in idents_non_local:
                is_found = False
                # look for this var in it dominatores
                for d_b_id in dominators:
                    if d_b_id == block_id:
                        # do not consider itself
                        continue
                    if ident[0] in block_ident_gen[d_b_id]:
                        is_found = True
                        break
                if is_found == False:
                    idents_left.append(ident)
                # for those vars that cannot be found in its domiators, backtrace to 
                # test if there is a path along wich the var is not defined. 
            path_constraint = None
            if len(block.predecessors) ==1:
                path_constraint = block.predecessors[0].exitcase
            for ident in idents_left:
                visited = set()
                dom_stmt_res = []
                is_found = self.backward_query_new(block, ident[0], visited, dom={}, block_ident_gen=block_ident_gen, condition_cons=path_constraint, entry_id=cfg.entryblock.id, idom=idom,
                        dom_stmt_res=dom_stmt_res) 
                if is_found:
                    idom_block_id = idom[block.id]
                    idom_block = id2block[idom_block_id]
                    stmt_type = type(idom_block.statements[-1])
                    dom_stmt_res.append(stmt_type)
                    print(ident[0], dom_stmt_res)

                    undefined_names += [ident]

        return list(set(undefined_names)) 
    def backward_query_stmt_type(self, block, ident_name, visited, dom={},idom = {}, dom_stmt_res = [],  block_ident_gen={}, condition_cons=None, entry_id=1):
        # condition constraints:
        phi_fun = []
        visited.add(block.id)
        path.append(block.id)
        # all the incoming path
        # if this is the entry block and ident not in the gen set then return True
        if block.id == entry_id:
            return True
        for suc_link in block.predecessors: 
            if condition_cons is not None and suc_link.exitcase is not None: 
                this_condition = invert(condition_cons) 
                this_txt = astor.to_source(this_condition) 
                this_edge_txt = astor.to_source(suc_link.exitcase)
                # this path contracdict the constraints
                if this_txt.strip()==this_edge_txt.strip():
                    continue
            parent_block = suc_link.source
            target_block = suc_link.target
            # deal with cycles, this is back edge
            if parent_block is None:
                continue
            if parent_block.id in visited or parent_block.id == block.id:
                continue
            # if the block dominates the parent block, then give it up
            if parent_block.id in dom and  block.id in dom[parent_block.id]:
                continue
            ##############
            if parent_block.id not in block_ident_gen:
                continue
            # if the name id found in this gen set. then stop visiting this path
            if ident_name in block_ident_gen[parent_block.id]:
                continue
                return True
            # if the name id is not found in the parent block and the parent is entry  return True
            if parent_block.id == entry_id:
                return False
            # if continue to search
            # not in its parent gen set  then search from this path
            return self.backward_query_new(parent_block, ident_name, visited, dom=dom, block_ident_gen=block_ident_gen, condition_cons=condition_cons, entry_id=entry_id) 
        return False
    # if there exists one path that ident_name is not reachable 
    def backward_query_new(self, block, ident_name, visited, path = [], dom={},idom = {}, dom_stmt_res = [],  block_ident_gen={}, condition_cons=None, entry_id=1):
        # condition constraints:
        phi_fun = []
        visited.add(block.id)
        path.append(block.id)
        # all the incoming path
        # if this is the entry block and ident not in the gen set then return True
        if block.id == entry_id:
            return True
        for suc_link in block.predecessors: 
            if condition_cons is not None and suc_link.exitcase is not None: 
                this_condition = invert(condition_cons) 
                this_txt = astor.to_source(this_condition) 
                this_edge_txt = astor.to_source(suc_link.exitcase)
                # this path contracdict the constraints
                if this_txt.strip()==this_edge_txt.strip():
                    continue
            parent_block = suc_link.source
            target_block = suc_link.target
            # deal with cycles, this is back edge
            if parent_block is None:
                continue
            if parent_block.id in visited or parent_block.id == block.id:
                continue
            # if the block dominates the parent block, then give it up
            if parent_block.id in dom and  block.id in dom[parent_block.id]:
                continue
            ##############
            if parent_block.id not in block_ident_gen:
                continue
            # if the name id found in this gen set. then stop visiting this path
            if ident_name in block_ident_gen[parent_block.id]:
                continue
            # if the name id is not found in the parent block and the parent is entry  return True
            if parent_block.id == entry_id:
                return True
            # if continue to search
            # not in its parent gen set  then search from this path
            return self.backward_query_new(parent_block, ident_name, visited, dom=dom, block_ident_gen=block_ident_gen, condition_cons=condition_cons, entry_id=entry_id) 
        return False

    def compute_SSA(self, cfg, live_ident_table={}, is_final=False):
        """
        generate an SSA graph.
        """
        # to consider single line function call / single line attributes/
        # return statements
        self.get_global_live_vars()
        #self.numbering = {}
        # visit all blocks in bfs order 
        all_blocks = cfg.get_all_blocks()
        self.compute_dom(all_blocks)
        for block in all_blocks:
            #assign_records = self.get_assign_raw(block.statements)
            ident_records = self.get_stmt_idents_ctx(block.statements)
            for stored_idents, loaded_idents in ident_records:
                phi_fun = []
                for var_name in loaded_idents:
                   # last assignment occur in the same block
                    for tmp_var_no in reversed(list(block.ssa_form.keys())):
                        if var_name == tmp_var_no[0]:
                            phi_fun.append(tmp_var_no)
                            break
                local_block_vars = [tmp[0] for tmp in phi_fun]
                remaining_vars = [tmp for tmp in loaded_idents if tmp not in local_block_vars and (tmp not in stored_idents)]
                phi_fun = []
                for var_name in remaining_vars:
                    visited = set()
                    phi_fun_incoming = self.backward_query(block, var_name, visited)
                    if len(phi_fun_incoming) == 0:
                        phi_fun += [(var_name, -1)]
                    else:
                        phi_fun += phi_fun_incoming
                if len(stored_idents) == 0:
                    stored_idents += ["<holder>"]
                    #block.ssa_form[("<holder>", 1)] = phi_fun
                    #continue

                for ident_name in stored_idents:
                    if ident_name in self.numbering:
                        var_no = self.numbering[ident_name]+1
                        self.numbering[ident_name] = var_no
                    #    self.var_values[(left_name,var_no)] = actual_value
                        block.ssa_form[(ident_name, var_no)] = phi_fun
                    else:
                        var_no = 1
                        self.numbering[ident_name] = var_no
                        block.ssa_form[(ident_name, var_no)] = phi_fun
                        #    self.var_values[(left_name,var_no)] = actual_value

        self.ssa_blocks = all_blocks

    def is_undefined(self, load_idents):
        ident_phi_fun = {}
        for item in load_idents:
            if item[0] in ident_phi_fun:
                pass

    def to_json(self):
        pass

    def build_viz(self):
        pass

    def compute_final_idents(self):
        # when there is only one exit block, compute SSA for all the vars in
        # numbering make a if statement here to see if this is a module
        final_phi_fun = {}
        def_reach = {}
        for block in self.ssa_blocks:
            if len(block.exits) == 0:
                #for ident_name, phi_rec in block.ssa_form.items():
                #    print(ident_name, phi_rec)
                for ident_name, number in self.numbering.items():
                    visited = set()
                    phi_fun_incoming = self.backward_query(block, ident_name, visited)
                    if ident_name not in def_reach:
                        def_reach[ident_name] = set([tmp[1] for tmp in phi_fun_incoming])
                #for ident_name, nums in def_reach.items():
                #    print(ident_name, set(nums))
        return def_reach

    def find_this_ident_name(self, ident_name, live_ident_table, def_names):
        n_scopes = len(live_ident_table)
        for i in range(n_scopes):
            if ident_name in live_ident_table[-i]:
                if (-1 in live_ident_table[-i][ident_name]):
                    return False
                else:
                    return True
        if ident_name in BUILT_IN_FUNCTIONS:
            return True
        if ident_name not in def_names:
            return False
        return True

    def retrieve_key_stmts(self, block_id_lst):
        import astor
        id2blocks = {b.id:b for b in self.ssa_blocks}
        for b_id in block_id_lst:
            tmp_block = id2blocks[b_id]
            key_stmt = tmp_block.statements[-1]
            #print(astor.to_source(key_stmt))

    def print_block(self, block):
        #for stmt in block.statements:
        print(block.get_source())

    # compute the dominators 
    def compute_idom(self, ssa_blocks):
        # construct the Graph
        entry_block = ssa_blocks[0]
        G = nx.DiGraph()
        for block in ssa_blocks: 
            G.add_node(block.id)
            exits = block.exits
            preds =  block.predecessors
            for link in preds+exits:
                G.add_edge(link.source.id, link.target.id)
        #DF = nx.dominance_frontiers(G, entry_block.id)
        idom = nx.immediate_dominators(G, entry_block.id)
        return idom

    def RD(self, cfg_blocks):
        # worklist 
        entry_block = cfg_blocks[0]
        Out[entry_block.id]  = set()
        # init the iterative algorithm
        for block in cfg_blocks:
            if block.id != entry_block.id:
                out[block.id] = set()
        changed = True
        while changed:
            for block in cfg_blocks:
                # 
                pre_links = block.predecessors
                pre_blocks = [pl.source for pl in pre_links]
                pre_outs = [out[pb.id] for pb in pre_blocks]
                In[block.id] =  reduce(set.intersection, pre_outs) 
                Out[block.id] = gen(B) (In[block.id]-kill[block.id])
        # boundry
        return 0

    def compute_dom_old(self, ssa_blocks):
        entry_block = ssa_blocks[0]
        id2blocks = {b.id:b for b in ssa_blocks}
        block_ids = list(id2blocks.keys())
        entry_id = entry_block.id
        N_blocks = len(ssa_blocks)
        dom = {}
        # for all other nodes, set all nodes as the dominators
        for b_id in block_ids:
            if b_id == entry_id:
                dom[b_id] = set([entry_id])
            else:
                dom[b_id] = set(block_ids)

        # Iteratively eliminate nodes that are not dominators
        #Dom(n) = {n} union with intersection over Dom(p) for all p in pred(n)
        changed = True
        counter = 0
        while changed:
            changed = False
            for b_id in block_ids:
                if b_id == entry_id:
                    continue
                pre_block_ids = [pre_link.source.id for pre_link in id2blocks[b_id].predecessors ]
                pre_dom_set = [dom[pre_b_id] for pre_b_id in pre_block_ids if pre_b_id in dom]
                new_dom_set = set([b_id])

                if len(pre_dom_set) != 0:
                    new_dom_tmp = reduce(set.intersection, pre_dom_set) 
                    new_dom_set = new_dom_set.union(new_dom_tmp)
                old_dom_set = dom[b_id]

                if new_dom_set != old_dom_set:
                    changed = True
                    dom[b_id] = new_dom_set
        return dom

