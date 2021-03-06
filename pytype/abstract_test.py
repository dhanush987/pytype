"""Tests for abstract.py."""

import unittest


from pytype import abstract
from pytype import config
from pytype import errors
from pytype import vm
from pytype.pytd import cfg

import unittest


def binding_name(binding):
  """Return a name based on the variable name and binding position."""
  var = binding.variable
  return "%s:%d" % (var.name, var.bindings.index(binding))


class FakeFrame(object):

  def __init__(self):
    self.current_opcode = None


class AbstractTestBase(unittest.TestCase):

  def setUp(self):
    self._vm = vm.VirtualMachine(errors.ErrorLog(), config.Options([""]))
    self._program = cfg.Program()
    self._node = self._program.NewCFGNode("test_node")

  def new_var(self, name, *values):
    """Create a Variable bound to the given values."""
    var = self._program.NewVariable(name)
    for value in values:
      var.AddBinding(value, source_set=(), where=self._node)
    return var

  def new_dict(self, **kwargs):
    """Create a Dict from keywords mapping names to Variable objects."""
    d = abstract.Dict("dict", self._vm, self._node)
    for name, var in kwargs.items():
      d.set_str_item(self._node, name, var)
    return d


class InstanceTest(AbstractTestBase):

  # TODO(dbaum): Is it worth adding a test for frozenset()?  There isn't
  # an easy way to create one directly from the vm, it is already covered
  # in test_splits.py, and there aren't any new code paths.  Perhaps it isn't
  # worth the effort.

  def test_compatible_with_non_container(self):
    # Compatible with either True or False.
    i = abstract.Instance(
        self._vm.convert.object_type, self._vm, self._node)
    self.assertIs(True, i.compatible_with(True))
    self.assertIs(True, i.compatible_with(False))

  def test_compatible_with_list(self):
    i = abstract.Instance(
        self._vm.convert.list_type, self._vm, self._node)
    i.init_type_parameters("T")
    # Empty list is not compatible with True.
    self.assertIs(False, i.compatible_with(True))
    self.assertIs(True, i.compatible_with(False))
    # Once a type parameter is set, list is compatible with True and False.
    i.merge_type_parameter(self._node, "T", self._vm.convert.object_type)
    self.assertIs(True, i.compatible_with(True))
    self.assertIs(True, i.compatible_with(False))

  def test_compatible_with_set(self):
    i = abstract.Instance(
        self._vm.convert.set_type, self._vm, self._node)
    i.init_type_parameters("T")
    # Empty list is not compatible with True.
    self.assertIs(False, i.compatible_with(True))
    self.assertIs(True, i.compatible_with(False))
    # Once a type parameter is set, list is compatible with True and False.
    i.merge_type_parameter(self._node, "T", self._vm.convert.object_type)
    self.assertIs(True, i.compatible_with(True))
    self.assertIs(True, i.compatible_with(False))

  def test_compatible_with_none(self):
    # This test is specifically for abstract.Instance, so we don't use
    # self._vm.convert.none, which is an AbstractOrConcreteValue.
    i = abstract.Instance(
        self._vm.convert.none_type, self._vm, self._node)
    self.assertIs(False, i.compatible_with(True))
    self.assertIs(True, i.compatible_with(False))


class DictTest(AbstractTestBase):

  def setUp(self):
    super(DictTest, self).setUp()
    self._d = abstract.Dict("test_dict", self._vm, self._node)
    self._var = self._program.NewVariable("test_var")
    self._var.AddBinding(abstract.Unknown(self._vm))

  def test_compatible_with__when_empty(self):
    self.assertIs(False, self._d.compatible_with(True))
    self.assertIs(True, self._d.compatible_with(False))

  @unittest.skip("setitem() does not update the parameters")
  def test_compatible_with__after_setitem(self):
    # Once a slot is added, dict is ambiguous.
    self._d.setitem(self._node, self._var, self._var)
    self.assertIs(True, self._d.compatible_with(True))
    self.assertIs(True, self._d.compatible_with(False))

  def test_compatible_with__after_set_str_item(self):
    # set_str_item() will make the dict ambiguous.
    self._d.set_str_item(self._node, "key", self._var)
    self.assertIs(True, self._d.compatible_with(True))
    self.assertIs(True, self._d.compatible_with(False))

  @unittest.skip("update() does not update the parameters")
  def test_compatible_with__after_update(self):
    # Updating an empty dict also makes it ambiguous.
    self._d.update(self._node, abstract.Unknown(self._vm))
    self.assertIs(True, self._d.compatible_with(True))
    self.assertIs(True, self._d.compatible_with(False))


class IsInstanceTest(AbstractTestBase):

  def setUp(self):
    super(IsInstanceTest, self).setUp()
    self._is_instance = abstract.IsInstance(self._vm)
    # Easier access to some primitive instances.
    self._bool = self._vm.convert.primitive_class_instances[bool]
    self._int = self._vm.convert.primitive_class_instances[int]
    self._str = self._vm.convert.primitive_class_instances[str]
    # Values that represent primitive classes.
    self._obj_class = abstract.get_atomic_value(
        self._vm.convert.primitive_classes[object])
    self._int_class = abstract.get_atomic_value(
        self._vm.convert.primitive_classes[int])
    self._str_class = abstract.get_atomic_value(
        self._vm.convert.primitive_classes[str])

  def assert_call(self, expected, left, right):
    """Check that call() returned the desired results.

    Args:
      expected: A dict from values to source sets, where a source set is
          represented by the sorted binding names separated by spaces, for
          example "left:0 right:1" would indicate binding #0 of variable
          "left" and binding #1 of variable "right".
      left: A Variable to use as the first arg to call().
      right: A Variable to use as the second arg to call().
    """
    node, result = self._is_instance.call(
        self._node, None, abstract.FunctionArgs((left, right), self.new_dict(),
                                                None, None))
    self.assertEquals(self._node, node)
    result_map = {}
    # Turning source sets into canonical string representations of the binding
    # names makes it much easier to debug failures.
    for b in result.bindings:
      terms = set()
      for o in b.origins:
        self.assertEquals(self._node, o.where)
        for sources in o.source_sets:
          terms.add(" ".join(sorted(binding_name(b) for b in sources)))
      result_map[b.data] = terms
    self.assertEquals(expected, result_map)

  def test_call_single_bindings(self):
    right = self.new_var("right", self._str_class)
    self.assert_call(
        {self._vm.convert.true: {"left:0 right:0"}},
        self.new_var("left", self._str),
        right)
    self.assert_call(
        {self._vm.convert.false: {"left:0 right:0"}},
        self.new_var("left", self._int),
        right)
    self.assert_call(
        {self._bool: {"left:0 right:0"}},
        self.new_var("left", abstract.Unknown(self._vm)),
        right)

  def test_call_multiple_bindings(self):
    self.assert_call(
        {
            self._vm.convert.true: {"left:0 right:0", "left:1 right:1"},
            self._vm.convert.false: {"left:0 right:1", "left:1 right:0"},
        },
        self.new_var("left", self._int, self._str),
        self.new_var("right", self._int_class, self._str_class)
    )

  def test_call_wrong_argcount(self):
    self._vm.push_frame(FakeFrame())
    node, result = self._is_instance.call(
        self._node, None, abstract.FunctionArgs((), self.new_dict(),
                                                None, None))
    self.assertEquals(self._node, node)
    self.assertIsInstance(abstract.get_atomic_value(result),
                          abstract.Unsolvable)
    self.assertRegexpMatches(
        str(self._vm.errorlog),
        r"isinstance .* 0 args .* expected 2.*\[wrong-arg-count\]")

  def test_call_wrong_keywords(self):
    self._vm.push_frame(FakeFrame())
    x = self.new_var("x", abstract.Unknown(self._vm))
    node, result = self._is_instance.call(
        self._node, None, abstract.FunctionArgs((x, x), self.new_dict(foo=x),
                                                None, None))
    self.assertEquals(self._node, node)
    self.assertIsInstance(abstract.get_atomic_value(result),
                          abstract.Unsolvable)
    self.assertRegexpMatches(
        str(self._vm.errorlog),
        r"foo.*isinstance.*\[wrong-keyword-args\]")

  def test_is_instance(self):
    def check(expected, left, right):
      self.assertEquals(expected, self._is_instance._is_instance(left, right))

    obj_class = self._vm.convert.primitive_classes[object].bindings[0].data

    # Unknown and Unsolvable are ambiguous.
    check(None, abstract.Unknown(self._vm), obj_class)
    check(None, abstract.Unsolvable(self._vm), obj_class)

    # If the object's class has multiple bindings, result is ambiguous.
    obj = abstract.SimpleAbstractValue("foo", self._vm)
    check(None, obj, obj_class)
    obj.set_class(self._node, self.new_var(
        "foo_class", self._str_class, self._int_class))
    check(None, obj, self._str_class)

    # If the class_spec is not a class, result is ambiguous.
    check(None, self._str, self._str)

    # Result is True/False depending on if the class is in the object's mro.
    check(True, self._str, obj_class)
    check(True, self._str, self._str_class)
    check(False, self._str, self._int_class)

  def test_flatten(self):
    def maybe_var(v):
      return v if isinstance(v, cfg.Variable) else self.new_var("v", v)

    def new_tuple(*args):
      pyval = tuple(maybe_var(a) for a in args)
      return abstract.AbstractOrConcreteValue(
          pyval, self._vm.convert.tuple_type, self._vm, self._node)

    def check(expected_ambiguous, expected_classes, value):
      classes = []
      ambiguous = self._is_instance._flatten(value, classes)
      self.assertEquals(expected_ambiguous, ambiguous)
      self.assertEquals(expected_classes, classes)

    unknown = abstract.Unknown(self._vm)

    # Simple values.
    check(False, [self._str_class], self._str_class)
    check(True, [], self._str)
    check(True, [], unknown)

    # (str, int)
    check(False, [self._str_class, self._int_class],
          new_tuple(self._str_class, self._int_class))
    # (str, ?, int)
    check(True, [self._str_class, self._int_class],
          new_tuple(self._str_class, unknown, self._int_class))
    # (str, (int, object))
    check(False, [self._str_class, self._int_class, self._obj_class],
          new_tuple(
              self._str_class,
              new_tuple(self._int_class, self._obj_class)))
    # (str, (?, object))
    check(True, [self._str_class, self._obj_class],
          new_tuple(
              self._str_class,
              new_tuple(unknown, self._obj_class)))
    # A variable with multiple bindings is ambiguous.
    # (str, int | object)
    check(True, [self._str_class],
          new_tuple(self._str_class,
                    self.new_var("v", self._int_class, self._obj_class)))


if __name__ == "__main__":
  unittest.main()
