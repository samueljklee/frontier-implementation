from urlFrontier import Frontier
from app import *
import unittest
import requests
import time

frontierFunc = Frontier()

class TestUrlFrontierComponents(unittest.TestCase):

    def test_1_prioritizer_input_output(self):
        expected_output = {'id': 'dd91548b36491b2e96ac31819a5d313a', 
                            'url': 'https://www.phonearena.com', 
                            'last_request_at': 1532940651, 
                            'last_request_time': 3, 
                            'final_page': True, 
                            'white_list': True}
        self.assertEqual(frontierFunc.prioritizer("https://www.phonearena.com", 1532940651, 3, True, True), expected_output)
        
    def test_2_front_end_queue_selector(self):
        frontierFunc.prioritizer("https://spectrum.ieee.org", 1533096053, 2, True, False)

        expected_output = {'id': '3920ad4b6d97c7b7d1fffbba7ed9b952', 
                            'url': 'https://spectrum.ieee.org', 
                            'last_request_at': 1533096053, 
                            'last_request_time': 2, 
                            'final_page': True, 
                            'white_list': False}

        self.assertEqual(frontierFunc.front_end_queue_selector(), expected_output)

    def test_3_back_end_queue_router(self):
        frontierFunc.prioritizer("https://spectrum.ieee.org", 1533096053, 2, True, False)

        expected_output = {'www.phonearena.com': [{'id': 'dd91548b36491b2e96ac31819a5d313a', 
                                                'url': 'https://www.phonearena.com', 
                                                'last_request_at': 1532940651, 
                                                'last_request_time': 3, 
                                                'final_page': True, 
                                                'white_list': True}], 
                            'spectrum.ieee.org': [{'id': '3920ad4b6d97c7b7d1fffbba7ed9b952', 
                                                'url': 'https://spectrum.ieee.org', 
                                                'last_request_at': 1533096053, 
                                                'last_request_time': 2, 
                                                'final_page': True, 
                                                'white_list': False}]}


        self.assertEqual(frontierFunc.back_end_queue_router(), expected_output)

    def test_4_back_end_queue_selector(self):
        expected_output = {'id': 'dd91548b36491b2e96ac31819a5d313a', 
                            'url': 'https://www.phonearena.com', 
                            'last_request_at': 1532940651, 
                            'last_request_time': 3, 
                            'final_page': True, 
                            'white_list': True}

        self.assertEqual(frontierFunc.back_end_queue_selector(), expected_output)

    def test_5_commit_message(self):
        hostname = 'spectrum.ieee.org'
        data = {'id': '3920ad4b6d97c7b7d1fffbba7ed9b952', 
                'url': 'https://spectrum.ieee.org', 
                'last_request_at': 1533096053, 
                'last_request_time': 2, 
                'final_page': True, 
                'white_list': False}
        id = '3920ad4b6d97c7b7d1fffbba7ed9b952'
        expected_output = {'status': 'Successfully commit message id {}'.format(id)}

        frontierFunc.start_commit_message_thread(hostname, data)
        self.assertEqual(frontierFunc.commit_message(id), expected_output)

    def tearDown(self):
        time.sleep(1)

if __name__ == "__main__":
    unittest.main(verbosity=2)