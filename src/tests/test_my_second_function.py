# <project_root>/tests/test_my_second_function.py
import unittest
import azure.functions as func

from function_app import main

class TestFunction(unittest.TestCase):
  def test_my_second_function(self):
    # Construct a mock HTTP request.
    req = func.HttpRequest(method='GET',
                           body=None,
                           url='/api/my_second_function',
                           params={'value': '21'})
    # Call the function.
    func_call = main.build().get_user_function()
    resp = func_call(req)
    # Check the output.
    self.assertEqual(
        resp.get_body(),
        b'21 * 2 = 42',
    )
    
