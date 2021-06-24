import unittest

class CCPatternTestCase(unittest.TestCase):

    @unittest.SkipTest
    def test_pattern(self):
        self.assertEqual(0, 1 - 1)

        """ Teststrings: 
        
        This is a string (abc)
        (abc)
        SIMON: abcd
        SIMON:abcd
        SIMON abcd
        THis is a string
        MY LINE
        MYD
        MYD.SDF
        """




if __name__ == '__main__':
    unittest.main()
