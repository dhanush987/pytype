"""Test functions etc, for Byterun."""



from pytype import utils
from pytype.tests import test_inference


class TestFunctions(test_inference.InferenceTest):

  def test_functions(self):
    self.assertNoErrors("""\
      def fn(a, b=17, c="Hello", d=[]):
        d.append(99)
        print(a, b, c, d)
      fn(1)
      fn(2, 3)
      fn(3, c="Bye")
      fn(4, d=["What?"])
      fn(5, "b", "c")
      """)

  def test_function_locals(self):
    self.assertNoErrors("""\
      def f():
        x = "Spite"
        print(x)
      def g():
        x = "Malice"
        print(x)
      x = "Humility"
      f()
      print(x)
      g()
      print(x)
      """)

  def test_recursion(self):
    self.assertNoErrors("""\
      def fact(n):
        if n <= 1:
          return 1
        else:
          return n * fact(n-1)
      f6 = fact(6)
      print(f6)
      assert f6 == 720
      """)

  def test_calling_functions_with_args_kwargs(self):
    self.assertNoErrors("""\
      def fn(a, b=17, c="Hello", d=[]):
        d.append(99)
        print(a, b, c, d)
      fn(6, *[77, 88])
      fn(**{'c': 23, 'a': 7})
      fn(6, *[77], **{'c': 23, 'd': [123]})
      """)

  def test_calling_functions_with_generator_args(self):
    self.assertNoErrors("""\
      class A(object):
        def next(self):
          raise StopIteration()
        def __iter__(self):
          return A()
      def f(*args):
        pass
      f(*A())
    """)

  def test_defining_functions_with_args_kwargs(self):
    self.assertNoErrors("""\
      def fn(*args):
        print("args is %r" % (args,))
      fn(1, 2)
      """)
    self.assertNoErrors("""\
      def fn(**kwargs):
        print("kwargs is %r" % (kwargs,))
      fn(red=True, blue=False)
      """)
    self.assertNoErrors("""\
      def fn(*args, **kwargs):
        print("args is %r" % (args,))
        print("kwargs is %r" % (kwargs,))
      fn(1, 2, red=True, blue=False)
      """)
    self.assertNoErrors("""\
      def fn(x, y, *args, **kwargs):
        print("x is %r, y is %r" % (x, y))
        print("args is %r" % (args,))
        print("kwargs is %r" % (kwargs,))
      fn('a', 'b', 1, 2, red=True, blue=False)
      """)

  def test_defining_functions_with_empty_args_kwargs(self):
    self.assertNoErrors("""\
      def fn(*args):
        print("args is %r" % (args,))
      fn()
      """)
    self.assertNoErrors("""\
      def fn(**kwargs):
        print("kwargs is %r" % (kwargs,))
      fn()
      """)
    self.assertNoErrors("""\
      def fn(*args, **kwargs):
        print("args is %r, kwargs is %r" % (args, kwargs))
      fn()
      """)

  def test_partial(self):
    self.assertNoErrors("""\
      from _functools import partial

      def f(a,b):
        return a-b

      f7 = partial(f, 7)
      four = f7(3)
      assert four == 4
      """)

  def test_partial_with_kwargs(self):
    self.assertNoErrors("""\
      from _functools import partial

      def f(a,b,c=0,d=0):
        return (a,b,c,d)

      f7 = partial(f, b=7, c=1)
      them = f7(10)
      assert them == (10,7,1,0)
      """)

  def test_wraps(self):
    self.assertNoErrors("""\
      from functools import wraps
      def my_decorator(f):
        dec = wraps(f)
        def wrapper(*args, **kwds):
          print('Calling decorated function')
          return f(*args, **kwds)
        wrapper = dec(wrapper)
        return wrapper

      @my_decorator
      def example():
        '''Docstring'''
        return 17

      assert example() == 17
      """)


class TestClosures(test_inference.InferenceTest):

  def test_closures(self):
    self.assertNoErrors("""\
      def make_adder(x):
        def add(y):
          return x+y
        return add
      a = make_adder(10)
      print(a(7))
      assert a(7) == 17
      """)

  def test_closures_store_deref(self):
    self.assertNoErrors("""\
      def make_adder(x):
        z = x+1
        def add(y):
          return x+y+z
        return add
      a = make_adder(10)
      print(a(7))
      assert a(7) == 28
      """)

  def test_closures_in_loop(self):
    self.assertNoErrors("""\
      def make_fns(x):
        fns = []
        for i in range(x):
          fns.append(lambda i=i: i)
        return fns
      fns = make_fns(3)
      for f in fns:
        print(f())
      assert (fns[0](), fns[1](), fns[2]()) == (0, 1, 2)
      """)

  def test_closures_with_defaults(self):
    self.assertNoErrors("""\
      def make_adder(x, y=13, z=43):
        def add(q, r=11):
          return x+y+z+q+r
        return add
      a = make_adder(10, 17)
      print(a(7))
      assert a(7) == 88
      """)

  def test_deep_closures(self):
    self.assertNoErrors("""\
      def f1(a):
        b = 2*a
        def f2(c):
          d = 2*c
          def f3(e):
            f = 2*e
            def f4(g):
              h = 2*g
              return a+b+c+d+e+f+g+h
            return f4
          return f3
        return f2
      answer = f1(3)(4)(5)(6)
      print(answer)
      assert answer == 54
      """)

class TestGenerators(test_inference.InferenceTest):

  def test_first(self):
    self.assertNoErrors("""\
      def two():
        yield 1
        yield 2
      for i in two():
        print(i)
      """)

  def test_partial_generator(self):
    self.assertNoErrors("""\
      from _functools import partial

      def f(a,b):
        num = a+b
        while num:
          yield num
          num -= 1

      f2 = partial(f, 2)
      three = f2(1)
      assert list(three) == [3,2,1]
      """)

  def test_unsolvable(self):
    self.assertNoCrash("""\
      assert list(three) == [3,2,1]
      """)

  def test_yield_multiple_values(self):
    # TODO(kramm): The generator doesn't have __iter__?
    self.assertNoCrash("""\
      def triples():
        yield 1, 2, 3
        yield 4, 5, 6

      for a, b, c in triples():
        print(a, b, c)
      """)

  def test_generator_reuse(self):
    self.assertNoErrors("""\
      g = (x*x for x in range(5))
      print(list(g))
      print(list(g))
      """)

  def test_generator_from_generator2(self):
    self.assertNoErrors("""\
      g = (x*x for x in range(3))
      print(list(g))

      g = (x*x for x in range(5))
      g = (y+1 for y in g)
      print(list(g))
      """)

  def test_generator_from_generator(self):
    # TODO(kramm): The generator doesn't have __iter__?
    self.assertNoCrash("""\
      class Thing(object):
        RESOURCES = ('abc', 'def')
        def get_abc(self):
          return "ABC"
        def get_def(self):
          return "DEF"
        def resource_info(self):
          for name in self.RESOURCES:
            get_name = 'get_' + name
            yield name, getattr(self, get_name)

        def boom(self):
          #d = list((name, get()) for name, get in self.resource_info())
          d = [(name, get()) for name, get in self.resource_info()]
          return d

      print(Thing().boom())
      """)

  def test_pass_through_args(self):
    ty = self.Infer("""
      def f(a, b):
        return a * b
      def g(*args, **kwargs):
        return f(*args, **kwargs)
      g(1, 2)
    """, deep=False, solve_unknowns=False, extract_locals=False)
    self.assertHasReturnType(ty.Lookup("g"), self.int)

  def test_pass_through_kwargs(self):
    ty = self.Infer("""
      def f(a, b):
        return a * b
      def g(*args, **kwargs):
        return f(*args, **kwargs)
      g(a=1, b=2)
    """, deep=False, solve_unknowns=False, extract_locals=False)
    self.assertHasReturnType(ty.Lookup("g"), self.int)

  def test_closure(self):
    ty = self.Infer("""
      import ctypes
      f = 0
      def e():
        global f
        s = 0
        f = (lambda: ctypes.foo(s))  # ctypes.foo doesn't exist
        return f()
      e()
    """, deep=True, solve_unknowns=True, report_errors=False)
    self.assertHasReturnType(ty.Lookup("e"), self.anything)
    self.assertTrue(ty.Lookup("f"))

  def test_list_comprehension(self):
    ty = self.Infer("""
      def f(elements):
        return "%s" % ",".join(t for t in elements)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def f(elements) -> str
    """)

  def test_tuple_args_smoke(self):
    unused_ty = self.Infer("""
      def foo((x, y), z):
        pass
    """, deep=True, solve_unknowns=True)
    # Smoke test only. pytd doesn't support automatic tuple unpacking in args.

  def test_matching_functions(self):
    ty = self.Infer("""
      def f():
        return 3

      class Foo(object):
        def match_method(self):
          return map(self.method, [])
        def match_function(self):
          return map(f, [])
        def match_pytd_function(self):
          return map(map, [])
        def match_bound_pytd_function(self):
          return map({}.keys, [])
        def method(self):
          pass
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def f() -> int
      class Foo(object):
        def match_method(self) -> List[nothing, ...]
        def match_function(self) -> List[nothing, ...]
        def match_pytd_function(self) -> List[nothing, ...]
        def match_bound_pytd_function(self) -> List[nothing, ...]
        def method(self) -> NoneType
    """)

  def test_named_arg_unsolvable_max_depth(self):
    # Main test here is for this not to throw a KeyError exception while
    # runing type inference. The given options simulate those of --quick.
    _, errors = self.InferAndCheck("""
      def f(x):
        return max(foo=repr(__any_object__))
    """, deep=True, solve_unknowns=False, maximum_depth=1, extract_locals=True)
    self.assertEquals(1, len(errors))
    self.assertErrorLogContains(errors, r"iterable.*max.*\[missing-parameter\]")

  def test_multiple_signatures_with_type_parameter(self):
    with utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        T = TypeVar("T")
        def f(x: T, y: int) -> List[T]
        def f(x: List[T], y: str) -> List[T]
      """)
      ty = self.Infer("""
        import foo
        def f(x, y):
          return foo.f(x, y)
      """, pythonpath=[d.path], deep=True, solve_unknowns=True)
      self.assertTypesMatchPytd(ty, """
        foo = ...  # type: module
        def f(x, y: int or str) -> list
      """)

  def test_unknown_single_signature(self):
    # Test that the right signature is picked in the presence of an unknown
    with utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        T = TypeVar("T")
        def f(x: T, y: int) -> List[T]
        def f(x: List[T], y: str) -> List[T]
      """)
      ty = self.Infer("""
        import foo
        def f(y):
          return foo.f("", y)
      """, pythonpath=[d.path], deep=True, solve_unknowns=True)
      self.assertTypesMatchPytd(ty, """
        foo = ...  # type: module
        def f(y: int) -> List[str]
      """)

  def test_unknown_with_solved_type_parameter(self):
    with utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        T = TypeVar("T")
        def f(x: T, y: T) -> List[T]
        def f(x: List[T], y: T) -> List[T]
      """)
      ty = self.Infer("""
        import foo
        def f(x):
          return foo.f(x, "")
      """, pythonpath=[d.path], deep=True, solve_unknowns=True)
      self.assertTypesMatchPytd(ty, """
        foo = ...  # type: module
        # TODO(rechen): def f(x: str or List[str]) -> List[str]
        def f(x) -> list
      """)

  def test_unknown_with_extra_information(self):
    with utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        T = TypeVar("T")
        def f(x: T) -> List[T]
        def f(x: List[T]) -> List[T]
      """)
      ty = self.Infer("""
        import foo
        def f(x):
          return foo.f(x)[0].isnumeric()
        def g(x):
          return foo.f(x) + [""]
        def h(x):
          ret = foo.f(x)
          x += ""
          return ret
      """, pythonpath=[d.path], deep=True, solve_unknowns=True)
      self.assertTypesMatchPytd(ty, """
        foo = ...  # type: module
        # TODO(rechen): def f(unicode or List[unicode]) -> bool
        def f(x) -> Any
        # TODO(rechen): def g(x) -> list
        def g(x) -> Any
        # TODO(rechen): def h(x: bytearray or str or unicode) -> List[bytearray or str or unicode]
        def h(x: Any) -> list
      """)

  def test_type_parameter_in_return(self):
    with utils.Tempdir() as d:
      d.create_file("foo.pyi", """
        T = TypeVar("T")
        class MyPattern(Generic[T]):
          def match(self, string: T) -> MyMatch[T]
        class MyMatch(Generic[T]):
          pass
        def compile() -> MyPattern[T]: ...
      """)
      ty = self.Infer("""\
        import foo
        x = foo.compile().match("")
      """, deep=True, pythonpath=[d.path], solve_unknowns=True)
      self.assertTypesMatchPytd(ty, """
        import typing

        foo = ...  # type: module
        x = ...  # type: foo.MyMatch[str]
      """)


if __name__ == "__main__":
  test_inference.main()
