import unittest

from clisnips.strfmt.doc_parser import parse
from clisnips.strfmt.doc_nodes import (Parameter, ValueList, ValueRange,
                                       CodeBlock)


class DocParserTest(unittest.TestCase):

    def testParseFreeText(self):
        text = """
            This is the global description of the command.
            It's all text until a {parameter} is seen.
            A {param} must start a line (possibly indented).
        """
        doc = parse(text)
        self.assertEqual(doc.header, text)
        self.assertListEqual(doc.parameters.values(), [])

    def testParseParameter(self):
        text = 'Global doc\n{par1} (file) Param doc'
        doc = parse(text)
        self.assertEqual(doc.header, 'Global doc\n')
        self.assertIn('par1', doc.parameters)
        param = doc.parameters['par1']
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.name, 'par1')
        self.assertEqual(param.typehint, 'file')
        self.assertEqual(param.text, 'Param doc')

    def testParseValueList(self):
        # digit list
        text = '{par1} [1, *-2, 0.3]'
        doc = parse(text)
        self.assertIn('par1', doc.parameters)
        param = doc.parameters['par1']
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
        doc = parse(text)
        self.assertIn('par1', doc.parameters)
        param = doc.parameters['par1']
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
        doc = parse(text)
        self.assertIn('par1', doc.parameters)
        param = doc.parameters['par1']
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
        doc = parse(text)
        self.assertIn('par1', doc.parameters)
        param = doc.parameters['par1']
        hint = param.valuehint
        self.assertEqual(hint.step, 1)
        self.assertEqual(hint.default, 5)
        # default step
        text = '{par1} [0.1..0.25]'
        doc = parse(text)
        self.assertIn('par1', doc.parameters)
        param = doc.parameters['par1']
        hint = param.valuehint
        self.assertEqual(hint.step, 0.01)
        # default step
        text = '{par1} [1..1.255]'
        doc = parse(text)
        self.assertIn('par1', doc.parameters)
        param = doc.parameters['par1']
        hint = param.valuehint
        self.assertEqual(hint.step, 0.001)

    def testParseCodeBlock(self):
        code_str = '''\
import os.path
if params['infile'] and not params['outfile']:
    path, ext = os.path.splitext(params['infile'])
    params['outfile'] = path + '.mp4'
'''
        text = '''
{infile} (path) The input file
{outfile} (path) The output file
```
%s
```''' % code_str
        doc = parse(text)
        #
        self.assertIn('infile', doc.parameters)
        param = doc.parameters['infile']
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.name, 'infile')
        self.assertEqual(param.typehint, 'path')
        self.assertEqual(param.text, 'The input file\n')
        #
        self.assertIn('outfile', doc.parameters)
        param = doc.parameters['outfile']
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.name, 'outfile')
        self.assertEqual(param.typehint, 'path')
        self.assertEqual(param.text, 'The output file\n')
        #
        self.assertEqual(len(doc.code_blocks), 1)
        code = doc.code_blocks[0]
        self.assertIsInstance(code, CodeBlock)
        self.assertEqual(code.code, code_str)
        # execute code
        _vars = {
            'params': {
                'infile': '/foo/bar.wav',
                'outfile': ''
            }
        }
        code.execute(_vars)
        self.assertEqual(_vars['params']['outfile'], '/foo/bar.mp4')
