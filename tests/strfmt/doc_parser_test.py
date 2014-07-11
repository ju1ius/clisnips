import unittest

from clisnips.strfmt.doc_lexer import Lexer
from clisnips.strfmt.doc_parser import Parser
from clisnips.strfmt.doc_nodes import Parameter, ValueList, ValueRange


class DocParserTest(unittest.TestCase):

    def _parse(self, text):
        lexer = Lexer(text)
        parser = Parser(lexer)
        return parser.parse()

    def testParseFreeText(self):
        text = """
            This is the global description of the command.
            It's all text until a {parameter} is seen.
            A {param} must start a line (possibly indented).
        """
        doc = self._parse(text)
        self.assertEqual(doc.text, text)
        self.assertListEqual(doc.parameters, [])

    def testParseParameter(self):
        text = 'Global doc\n{par1} (file) Param doc'
        doc = self._parse(text)
        self.assertEqual(doc.text, 'Global doc\n')
        param = doc.parameters[0]
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.name, 'par1')
        self.assertEqual(param.typehint, 'file')
        self.assertEqual(param.text, 'Param doc')

    def testParseValueList(self):
        # digit list
        text = '{par1} [1, *-2, 0.3]'
        doc = self._parse(text)
        param = doc.parameters[0]
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.name, 'par1')
        self.assertIsNone(param.typehint)
        self.assertIsNone(param.text)
        values = param.valuehint
        self.assertIsInstance(values, ValueList)
        self.assertListEqual(values.values, [1, -2, 0.3])
        self.assertEqual(values.default, 1)
        # string list
        text = '{par1} ["foo", *"bar", "baz"]'
        doc = self._parse(text)
        param = doc.parameters[0]
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.name, 'par1')
        self.assertIsNone(param.typehint)
        self.assertIsNone(param.text)
        values = param.valuehint
        self.assertIsInstance(values, ValueList)
        self.assertListEqual(values.values, ["foo", "bar", "baz"])
        self.assertEqual(values.default, 1)

    def testParseValueRange(self):
        text = '{par1} [1..10:2*5]'
        doc = self._parse(text)
        param = doc.parameters[0]
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.name, 'par1')
        self.assertIsNone(param.typehint)
        self.assertIsNone(param.text)
        hint = param.valuehint
        self.assertIsInstance(hint, ValueRange)
        self.assertEqual(hint.start, 1)
        self.assertEqual(hint.end, 10)
        self.assertEqual(hint.step, 2)
        self.assertEqual(hint.default, 5)
        # default step
        text = '{par1} [1..10*5]'
        doc = self._parse(text)
        param = doc.parameters[0]
        hint = param.valuehint
        self.assertEqual(hint.step, 1)
        self.assertEqual(hint.default, 5)
        # default step
        text = '{par1} [0.1..0.25]'
        doc = self._parse(text)
        param = doc.parameters[0]
        hint = param.valuehint
        self.assertEqual(hint.step, 0.01)
        # default step
        text = '{par1} [1..1.255]'
        doc = self._parse(text)
        param = doc.parameters[0]
        hint = param.valuehint
        self.assertEqual(hint.step, 0.001)
