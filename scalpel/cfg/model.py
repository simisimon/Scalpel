"""
Control flow graph for Python programs.
"""

import ast
import sys 
import re
import token
import tokenize 
import astor

import graphviz as gv


class Block(object):
    """
    Basic block in a control flow graph.

    Contains a list of statements executed in a program without any control
    jumps. A block of statements is exited through one of its exits. Exits are
    a list of Links that represent control flow jumps.
    """

    __slots__ = ["id", "statements", "func_calls", "predecessors", "exits"]

    def __init__(self, id):
        # Id of the block.
        self.id = id
        # Statements in the block.
        self.statements = []
        # Calls to functions inside the block (represents context switches to
        # some functions' CFGs).
        self.func_calls = []
        # Links to predecessors in a control flow graph.
        self.predecessors = []
        # Links to the next blocks in a control flow graph.
        self.exits = []

    def __del__(self):
        self.statements.clear()
        self.func_calls.clear()
        self.predecessors.clear()
        self.exits.clear()

    def __str__(self):
        if self.statements:
            return "block:{}@{}".format(self.id, self.at())
        return "empty block:{}".format(self.id)

    def __repr__(self):
        txt = "{} with {} exits".format(str(self), len(self.exits))
        if self.statements:
            txt += ", body=["
            txt += ", ".join([ast.dump(node) for node in self.statements])
            txt += "]"
        return txt

    def at(self):
        """
        Get the line number of the first statement of the block in the program.
        """
        if self.statements and self.statements[0].lineno >= 0:
            return self.statements[0].lineno
        return None

    def is_empty(self):
        """
        Check if the block is empty.
        Returns:
            A boolean indicating if the block is empty (True) or not (False).
        """
        return len(self.statements) == 0
    '''
    def strip_comment(self, src):
        clean_src = ""

        prev_toktype = token.INDENT
        first_line = None
        last_lineno = -1
        last_col = 0

        tokgen = tokenize.generate_tokens(src)
        for toktype, ttext, (slineno, scol), (elineno, ecol), ltext in tokgen:
            if 0:   # Change to if 1 to see the tokens fly by.
                print("%10s %-14s %-20r %r" % (
                    tokenize.tok_name.get(toktype, toktype),
                    "%d.%d-%d.%d" % (slineno, scol, elineno, ecol),
                    ttext, ltext
                    ))
            if slineno > last_lineno:
                last_col = 0
            if scol > last_col:
                mod.write(" " * (scol - last_col))
            if toktype == token.STRING and prev_toktype == token.INDENT:
                # Docstring
                mod.write("#--")
            elif toktype == tokenize.COMMENT:
                # Comment
                mod.write("##\n")
            else:
                mod.write(ttext)
            prev_toktype = toktype
            last_col = ecol
            last_lineno = elineno
        '''
    def get_source(self):
        """
        Get a string containing the Python source code corresponding to the
        statements in the block.
        Returns:
            A string containing the source code of the statements.
        """
        src = "#" + str(self.id)+'\n'
        for statement in self.statements:
            if type(statement) in [ast.If, ast.For, ast.While, ast.With]:
                src += (astor.to_source(statement)).split('\n')[0] + "\n"
            elif type(statement) == ast.Try:
                src += (astor.to_source(statement)).split('\n')[0] + "\n"
            #elif type(statement) == ast.If:
            #    src += (astor.to_source(statement)).split('\n')[0] + "\n"
            elif type(statement) in [ast.FunctionDef,ast.AsyncFunctionDef,
                    ast.ClassDef]:
                src += (astor.to_source(statement)).split('\n')[0] + "...\n"
            elif type(statement) == ast.ClassDef:
                src += (astor.to_source(statement)).split('\n')[0] + "...\n"
            else:
                src += astor.to_source(statement)
        return src

    def get_calls(self):
        """
        Get a string containing the calls to other functions inside the block.

        Returns:
            A string containing the names of the functions called inside the
            block.
        """
        txt = ""
        for func_call_entry in self.func_calls:
            txt += func_call_entry['name'] + '\n'
        return txt


class Link(object):
    """
    Link between blocks in a control flow graph.

    Represents a control flow jump between two blocks. Contains an exitcase in
    the form of an expression, representing the case in which the associated
    control jump is made.
    """

    __slots__ = ["source", "target", "exitcase"]

    def __init__(self, source, target, exitcase=None):
        assert type(source) == Block, "Source of a link must be a block"
        assert type(target) == Block, "Target of a link must be a block"
        # Block from which the control flow jump was made.
        self.source = source
        # Target block of the control flow jump.
        self.target = target
        # 'Case' leading to a control flow jump through this link.
        self.exitcase = exitcase

    def __str__(self):
        return "link from {} to {}".format(str(self.source), str(self.target))

    def __repr__(self):
        if self.exitcase is not None:
            return "{}, with exitcase {}".format(str(self),
                                                 ast.dump(self.exitcase))
        return str(self)

    def get_exitcase(self):
        """
        Get a string containing the Python source code corresponding to the
        exitcase of the Link.

        Returns:
            A string containing the source code.
        """
        if self.exitcase:
            return astor.to_source(self.exitcase)
        return ""
    def __del__(self):
        self.source = None
        # Target block of the control flow jump.
        self.target = None
        # 'Case' leading to a control flow jump through this link.
        self.exitcase = None



class CFG(object):
    """
    Control flow graph (CFG).

    A control flow graph is composed of basic blocks and links between them
    representing control flow jumps. It has a unique entry block and several
    possible 'final' blocks (blocks with no exits representing the end of the
    CFG).
    """
    def __init__(self, name, asynchr=False):
        """
        The constructor of CFG class. Only name of this graph is required. 
        """
        assert type(name) == str, "Name of a CFG must be a string"
        assert type(asynchr) == bool, "Async must be a boolean value"
        # Name of the function or module being represented.
        self.name = name
        # Type of function represented by the CFG (sync or async). A Python
        # program is considered as a synchronous function (main).
        self.asynchr = asynchr
        # Entry block of the CFG.
        self.entryblock = None
        # Final blocks of the CFG.
        self.finalblocks = []
        # Sub-CFGs for functions defined inside the current CFG.
        self.functioncfgs = {}
        self.class_cfgs = {}

        self.function_args = {}
        self.class_args = {}

    def __del__(self):
        pass 
    
    def __str__(self):
        return "CFG for {}".format(self.name)

    def remove_comments(self, src):
        pass

    
    
    def get_all_blocks(self):
        """
        Get a list of code blocks in this CFG; This is generated by BFS order.

        Returns:
            A list of code blocks. 
        """
        import queue
        all_blocks = []
        
        visited = set()
        working_queue = queue.Queue() 
        working_queue.put(self.entryblock)

        while not working_queue.empty():
            block = working_queue.get()
            # this block has been visited 
            if block.id in visited:
                continue
            all_blocks.append(block)
            visited.add(block.id)
            for suc_link in block.exits:
                if suc_link.target.id not in visited:
                    working_queue.put(suc_link.target)
        return all_blocks
        #def dfs(start_block):
        #    # non-recurisve implementation of DFS search
   
    def __iter__(self):
        """
        Generator that yields all the blocks in the current graph, then
        recursively yields from any sub graphs
        """
        visited = set()
        to_visit = [self.entryblock]

        while to_visit:
            block = to_visit.pop(0)
            visited.add(block)
            for exit_ in block.exits:
                if exit_.target in visited or exit_.target in to_visit:
                    continue
                to_visit.append(exit_.target)
            yield block

        for subcfg in self.functioncfgs.values():
            yield from subcfg
    
    def _visit_blocks(self, graph, block, visited=[], calls=True):
        # Don't visit blocks twice.
        if block.id in visited:
            return

        nodelabel = block.get_source()
        graph.node(str(block.id), label=nodelabel)

        visited.append(block.id)
        # Show the block's function calls in a node.
        if calls and block.func_calls:
            calls_node = str(block.id)+"_calls"
            calls_label = block.get_calls().strip()
            graph.node(calls_node, label=calls_label,
                       _attributes={'shape': 'box'})
            graph.edge(str(block.id), calls_node, label="calls",
                       _attributes={'style': 'dashed'})
        # Recursively visit all the blocks of the CFG.
        for exit in block.exits:
            self._visit_blocks(graph, exit.target, visited, calls=calls)
            edgelabel = exit.get_exitcase().strip()
            graph.edge(str(block.id), str(exit.target.id), label=edgelabel)

    def _build_visual(self, format='pdf', calls=True):
        graph = gv.Digraph(name='cluster'+self.name, format=format,
                           graph_attr={'label': self.name})
        self._visit_blocks(graph, self.entryblock, visited=[], calls=False)
        return graph

    def build_visual(self, format, calls=True, show=True):
        """
        Build a visualisation of the CFG with graphviz and output it in a DOT
        file.

        Args:
            filename: The name of the output file in which the visualisation
                      must be saved.
            format: The format to use for the output file (PDF, ...).
            show: A boolean indicating whether to automatically open the output
                  file after building the visualisation.
        """
        graph = self._build_visual(format, calls)
        return graph

