"""Tests for --quick and --abort-on-complex."""

from pytype.pytd import cfg
from pytype.tests import test_inference


class QuickTest(test_inference.InferenceTest):
  """Tests for --quick and --abort-on-complex."""

  def testMaxDepth(self):
    ty = self.Infer("""
      class Foo(object):
        def __init__(self, elements):
          assert all(e for e in elements)
          self.elements = elements

        def bar(self):
          return self.elements
    """, deep=True, extract_locals=True, quick=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        elements = ...  # type: Any
        def __init__(self, elements: Any) -> None: ...
        def bar(self) -> Any: ...
    """)

  def testAbortOnComplex(self):
    self.assertRaises(cfg.ProgramTooComplexError, self.Infer, """
      if __any_object__:
        x = [1]
      else:
        x = [1j]
      x = x + x
      x = x + x
      x = x + x
      x = x + x
      x = x + x
      x = x + x
      x = x + x
    """, abort_on_complex=True)


if __name__ == "__main__":
  test_inference.main()
