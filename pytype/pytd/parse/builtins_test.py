

from pytype.pytd import pytd
from pytype.pytd.parse import builtins
from pytype.pytd.parse import visitors
import unittest


class UtilsTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.builtins = builtins.GetBuiltinsPyTD()

  def testGetBuiltinsPyTD(self):
    self.assertIsNotNone(self.builtins)
    # Will throw an error for unresolved identifiers:
    visitors.LookupClasses(self.builtins)

  def testHasMutableParameters(self):
    append = self.builtins.Lookup("__builtin__.list").Lookup("append")
    self.assertIsNotNone(append.signatures[0].params[0].mutated_type)

  def testHasCorrectSelf(self):
    update = self.builtins.Lookup("__builtin__.dict").Lookup("update")
    t = update.signatures[0].params[0].type
    self.assertIsInstance(t, pytd.GenericType)
    self.assertEquals(t.base_type, pytd.ClassType("__builtin__.dict"))

  def testHasObjectSuperClass(self):
    cls = self.builtins.Lookup("__builtin__.int")
    self.assertEquals(cls.parents, (pytd.ClassType("__builtin__.object"),))
    cls = self.builtins.Lookup("__builtin__.object")
    self.assertEquals(cls.parents, ())

  def testParsePyTD(self):
    """Test ParsePyTD()."""
    ast = builtins.ParsePyTD("a = ...  # type: int",
                             "<inline>", python_version=(2, 7, 6),
                             lookup_classes=True)
    a = ast.Lookup("a").type
    self.assertItemsEqual(a, pytd.ClassType("int"))
    self.assertIsNotNone(a.cls)  # verify that the lookup succeeded

  def testParsePredefinedPyTD(self):
    """Test ParsePredefinedPyTD()."""
    ast = builtins.ParsePredefinedPyTD(
        "builtins", "sys", python_version=(2, 7, 6))
    self.assertIsNotNone(ast.Lookup("sys.stderr"))


if __name__ == "__main__":
  unittest.main()
