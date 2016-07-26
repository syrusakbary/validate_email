# encoding: utf-8
import unittest

from validate_email import validate_email

class AddressPatternTests(unittest.TestCase):
    
    def test_ascii_regular(self):
        self.assertTrue(validate_email(r'someone@gmail.com'))
        self.assertTrue(validate_email(r'some.one@gmail.com'))
        self.assertTrue(validate_email(r'someone+plus@gmail.com'))
        
        self.assertFalse(validate_email(r'someone@gmail'))
        self.assertFalse(validate_email(r'someonegmail.com'))
        self.assertFalse(validate_email(r'@gmail.com'))
        self.assertFalse(validate_email(r'someone @gmail.com'))
        
    # All of the names below come from wikipedia:  
    #   https://en.wikipedia.org/wiki/International_email#Email_addresses

    def test_chinese_regular(self):
        self.assertTrue(validate_email(r'用户@例子.广告')) # Chinese

        self.assertFalse(validate_email(r'用户例子.广告')) # No @
        self.assertFalse(validate_email(r'用户@例子广告')) # No .
        self.assertFalse(validate_email(r'用户@例子.')) # Nothing after the .
        self.assertFalse(validate_email(r'@例子.广告')) # Nothing before the @

    def test_hindi_regular(self):
        self.assertTrue(validate_email(r'उपयोगकर्ता@उदाहरण.कॉम')) # Hindi

        self.assertFalse(validate_email(r'उपयोगकर्ताउदाहरण.कॉम')) # No @
        self.assertFalse(validate_email(r'उपयोगकर्ता@उदाहरणकॉम')) # No .
        self.assertFalse(validate_email(r'उपयोगकर्ता@उदाहरण.')) # Nothing after the .
        self.assertFalse(validate_email(r'@उदाहरण.कॉम')) # Nothing before the @

    def test_ukranian_regular(self):
        self.assertTrue(validate_email(r'юзер@екзампл.ком')) # Chinese

        self.assertFalse(validate_email(r'')) # No @
        self.assertFalse(validate_email(r'')) # No .
        self.assertFalse(validate_email(r'')) # Nothing after the .
        self.assertFalse(validate_email(r'')) # Nothing before the @

    def test_greek_regular(self):
        self.assertTrue(validate_email(r'θσερ@εχαμπλε.ψομ'))

        self.assertFalse(validate_email(r'θσερεχαμπλε.ψομ')) # No @
        self.assertFalse(validate_email(r'θσερ@εχαμπλεψομ')) # No .
        self.assertFalse(validate_email(r'θσερ@εχαμπλε.')) # Nothing after the .
        self.assertFalse(validate_email(r'@εχαμπλε.ψομ')) # Nothing before the @

    def test_german_regular(self):
        self.assertTrue(validate_email(r'Dörte@Sörensen.example.com'))

        self.assertFalse(validate_email(r'DörteSörensen.example.com')) # No @
        self.assertFalse(validate_email(r'Dörte@Sörensenexamplecom')) # No .
        self.assertFalse(validate_email(r'Dörte@Sörensen.')) # Nothing after the .
        self.assertFalse(validate_email(r'@Sörensen.example.com')) # Nothing before the @