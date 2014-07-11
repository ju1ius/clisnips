#coding=utf-8
import unittest
import sqlite3

from clisnips.database import word_tokenizer 


TEST_SCHEMA = '''
CREATE VIRTUAL TABLE test USING fts4(
    tokenize=unicode_words,
    value TEXT
);
'''

FIXTURES = [
    u'Фырре пэрпэтюа пырикюлёз экз мэль, мэнтётюм консэквюат ыт пэр, жят.',
    u'कीसे वैश्विक लाभान्वित मुक्त लाभो खयालात मुख्यतह ढांचा बलवान सुना',
    u'''\
取費報続生約保読縦上努象鈴昨負指。\
験十養持法代終謙幅義別展。\
    ''',
    u"Rem gutt Hären do. Brommt d'Bëscher dir as. Wäit Plett'len.",
    u'شبح إعلان تكاليف بـ المدن.'
]


class WordTokenizerTest(unittest.TestCase):

    @classmethod
    def setUpClass(klass):
        con = sqlite3.connect(':memory:')
        word_tokenizer.register(con)
        con.row_factory = sqlite3.Row
        con.executescript(TEST_SCHEMA)
        for text in FIXTURES:
            con.execute('insert into test(value) values(?)', (text,))
        klass.connection = con

    @classmethod
    def tearDownClass(klass):
        klass.connection.close()

    def testWordSearch(self):
        query = 'select * from test where test match :term'
        term = u'экз'
        row = self.connection.execute(query, {'term': term}).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['value'], FIXTURES[0])
        #
        term = u'मुक्त'
        row = self.connection.execute(query, {'term': term}).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['value'], FIXTURES[1])
        #
        term = u'験十養持法代終謙幅義別展'
        row = self.connection.execute(query, {'term': term}).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['value'], FIXTURES[2])
        #
        term = u'Wäit'
        row = self.connection.execute(query, {'term': term}).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['value'], FIXTURES[3])
        #
        term = u'المدن'
        row = self.connection.execute(query, {'term': term}).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['value'], FIXTURES[4])

    def testCaseFolding(self):
        query = 'select * from test where test match :term'
        #
        term = u'фырре' 
        row = self.connection.execute(query, {'term': term}).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['value'], FIXTURES[0])
        #
        term = u'wäit plett'
        row = self.connection.execute(query, {'term': term}).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['value'], FIXTURES[3])

    def testDiacritics(self):
        query = 'select * from test where test match :term'
        #
        term = u'wait'
        row = self.connection.execute(query, {'term': term}).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['value'], FIXTURES[3])
